# TorchTrade

### Description
TorshTrade is a Python-based cryptocurrency trading bot leveraging reinforcement learning strategies. The bot leverages CCXT for interacting with the exchange and retrieving training data, and coinmarketcap for obtaining additional data such as Bitcoin dominance, market capitalization of each coin, and USDT market cap. It also uses StableBaselines3 for training its agents. This bot provides an easy way to translate your trading concepts into an executable bot for either paper trading or live trading.
### Roadmap
1 - Building the DataProcessor class to handle data downloading, formatting, cleaning, and adding technical indicators, as well as additional metrics from the CoinMarketCap API such as Bitcoin Dominance. This class will be built with flexibility so that new data from other APIs, such as on-chain data and market sentiment, can easily be added.

2 - Designing fully configurable environments inspired by the tensorTrade framework which will enable traders to have trading environments that can be tailored to their needs.
  - The ActionScheme interprets and applies the agent’s actions to the environment.
  - The RewardScheme computes the reward for each time step based on the agent’s performance.
  - The Observer generates the next observation for the agent.
  - The Stopper determines whether or not the episode is over.
  - The Informer generates useful monitoring information at each time step.
  - The Renderer renders a view of the environment and interactions.
  
3 - Implementing paper and live trading 

4 - Exploring other advanced topics such as 

5 - 
##
I just want to note that there have been many recent alternatives to traditional neural networks that do not rely on backpropagation or storing the results of the forward pass.

Two examples are Neural Ordinary Differential Equations [Chen, 2017] and Deep Equilibrium Models (DEQ) [Bai, 2019]. The first performs both the forward pass and the backward pass by solving differential equations, while the latter does so by solving fixed-point equations.

DEQs have been particularly successful. They are theoretically well-understood, use significantly less memory than regular neural networks due to not requiring to store the results of the forward pass, and have achieved comparable or SOTA results in many different tasks.

There has also been some work in creating differentiable machine learning models based on optimizers such as Quadratic Programs [Amos, 2017], Semidefinite Programs [Wang, 2019] and even Integer Programs [Paulus, 2021].
These models can be trained using gradient-based optimization without storing intermediate results or using backpropagation, although their results are overall less impressive.

Interestingly, Zico Kolter (who has been involved with DEQs) has mentioned a few years ago that specialized hardware could be developed to solve fixed-point equations. This could greatly favor Deep Equilibrium Models by providing some of the benefits outlined in Hinton's paper.

Personally, I think there has been some overreaction to Hinton's paper.
## Resources
https://github.com/EconomistGrant/HTFE-tensortrade
https://github.com/StephanAkkerman/Crypto_OHLCV
https://colab.research.google.com/drive/1r9I-DJjrT-0JHbrB10NLFudZ7hQdOcdq#scrollTo=TGmOyZQztluv

