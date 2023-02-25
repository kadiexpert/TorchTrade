import gym
import numpy as np
from torchtrade.components import Clock,Broker,TradeDirection
from gym import spaces
from typing import List


class SimpleTradingEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    metadata = {"render.modes": ["human"]}

    def __init__(
        self,
        clock : Clock,
        broker : Broker,
        symbols : List[str],
        window_size:int
        ):
        super().__init__()
        self.broker  = broker
        self.clock  = clock
        self.symbols = symbols
        self.window_size = window_size
        #0 Do nothing/1 buy/2 sellf
        self.action_space = spaces.Discrete(3)
        self.features_count = 9 
        self.observation_space = gym.spaces.Box(0, np.inf, shape=(self.window_size,self.features_count ))
        self.observation: np.array = np.empty((0, self.features_count ))
        self.reward = 0
        
    def perform_action(self,action):
        ss = 0.02 
        rr = 1.5
        if action == 0: 
            return
        elif action == 1: 
            self.broker.openTrade("long",self.symbols[0],TradeDirection.LONG,1,1,stop_loss=ss,risk_reward=1.5)
        elif action == 2:
            self.broker.openTrade("short",self.symbols[0],TradeDirection.SHORT,1,1,stop_loss=ss,risk_reward=1.5)
        else:
            ValueError(f"Action {action} can't be handled")
        
    def step(self, action):
        #done
        done = False
        #perform action
        self.perform_action(action)
        #step forward
        self.clock.next()
        #get the reward (we doesn't count for discount here)
        self.reward = self.broker.get_additive_reward_percentage()-self.reward 
        #get the new observation
        self.observation =   self.observation [1:]
        new_mkt_data = self.broker.market.data.iloc[0].values.astype(float)
        self.observation = np.append(self.observation, [new_mkt_data], axis=0)
        
        return self.observation,self.reward,self.clock.has_reached_end(),{}

    def reset(self):
        self.clock.reset()
        self.broker.reset()
        self.reward = 0
        self.observation = np.empty((0, self.features_count ))
        while self.observation.shape[0]<self.window_size:
            # create a new array to append
            new_mkt_data = self.broker.market.data.iloc[0].values.astype(float)
            self.observation = np.append(self.observation, [new_mkt_data], axis=0)
            self.clock.next()
        return self.observation 

    def render(self, mode="human"):
        pass

    def close(self):
        pass