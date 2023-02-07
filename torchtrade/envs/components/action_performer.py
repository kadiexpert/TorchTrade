import abc
import gym
import numpy as np
from typing import final

class ActionPerformer(abc.ABC):
    """Abstract class for performing actions in a gym environment.
    """
    def __init__(self, env: gym.Env):
        """Initializes the observation and action spaces of the environment.

        Args:
            env (gym.Env): The gym environment.
        """
        self.observation_space = env.observation_space
        self.action_space = env.action_space
        
    @abc.abstractmethod
    def _perform_action(self, observation: np.ndarray) -> np.ndarray:
        """Performs the given action based on the observation.

        This is a private method to be implemented by the subclasses


        Args:
            observation (np.ndarray): The current observation of the environment.

        Returns:
            np.ndarray: The action to be performed.
        """
        pass
    
    @final
    def run(self, observation: np.ndarray) -> np.ndarray: 
        """Checks if the provided observation and the returned action are compatible with the environment space.

        Args:
            observation (np.ndarray): The current observation of the environment.

        Returns:
            np.ndarray: The action to be performed.

        Raises:
            ValueError: If the observation or the action is not compatible with the environment space.
        """
        if not self.observation_space.contains(observation):
             raise ValueError("The fed observation doesn't match with the observation space of the environment")
        action = self._perform_action(observation)
        if not self.action_space.contains(action):
            raise ValueError("The generated action doesn't match with the environment action space")
        else:
            return action