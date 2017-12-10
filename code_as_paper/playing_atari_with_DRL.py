"""Playing Atari with Deep Reinforcement Learning (NIPS 2013 Deep Learning Workshop)
video : https://www.youtube.com/watch?v=V7_cNTfm2i8&list=PLlMkM4tgfjnJhhd4wn5aj8fVTYJwIpWkS&index=6
reference site : http://karpathy.github.io/2016/05/31/rl/  'Deep Reinforcement Learning: Pong from Pixels """

import numpy as np
import _compat_pickle as pickle
import gym

# hyperparameters
H = 200 # number of hidden layer neurons
batch_size = 10
learning_rate = 1e-4
gamma = 0.99 # discount factor for reward
decay_rate = 0.99 # decay factor for RMSProp leaky sum of grad^2
resume = False
render = False

# model initialization
D = 80 * 80
if resume:
    model = pickle.load(open('sava.p', 'rb'))
else:
    model = {}
    model['W1'] = np.random.randn(H, D) / np.sqrt(D) # "Xavier" initialization
    model['W2'] = np.random.randn(H) / np.sqrt(H)

grad_buffer = {k : np.zeros_like(v) for k,v in model.items()}
rmsprop_cache = {k: np.zeros_like(v) for k,v in model.items()}

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))

def prepro(I):
    I = I[35:195]
    I = I[::2, ::2, 0]
    I[I== 144] = 0  # erase background (background type 1)
    I[I== 109] = 0  # erase background (background type 2)
    I[I != 0] = 1   # everything else (paddles, ball) just set to 1
    return I.astype(np.float).ravel()

def discount_rewards(r):
    discounted_r = np.zeros_like(r)
    running_add = 0

    for t in reversed(range(0, r.size)):
        if r[t] != 0: running_add = 0 # reset the sum, since this was a game boundary (pong specific!)
        running_add = running_add * gamma + r[t]
        discounted_r[t] = running_add
    return discounted_r

def policy_forward(x):
    h = np.dot(model['W1'], x)
    h[h<0] = 0
    logp = np.dot(model['W2'], h)
    p = sigmoid(logp)
    return p, h


def policy_backward(eph, epdlogp):
    """eph is array of intermediate hidden states """
    dW2 = np.dot(eph.T, epdlogp).ravel()
    dh = np.outer(epdlogp, model['W2'])
    dh[eph <= 0] = 0
    dW1 = np.dot(dh.T, eph)
    return {'W1':dW1, 'W2':dW2}

env = gym.make("Pong-v0")
observation = env.reset()
prev_x = None
xs,hs,dlogps,drs = [],[],[],[]
running_reward = None
reward_sum = 0
episode_number = 0
while True:
    if render: env.render()

    cur_x = prepro(observation)
    x = cur_x - prev_x if prev_x is not None else np.zeros(D)
    prev_x = cur_x

    aprob, h = policy_forward(x)
    action = 2 if np.random.uniform() < aprob else 3 # roll the dice!

    xs.append(x) # observation
    hs.append(h) ## hidden state
    y = 1 if action == 2 else 0
    dlogps.append(y-aprob)

