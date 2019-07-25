---
layout: post
title: NIPS 2014
comments: True
permalink: nips-2014
---

**Interesting papers from Deep Learning and Representation Learning Workshop**

NIPS is the biggest deep learning conference showcasing the latest and greatest in deep learning. Lately the breakthrough in the field has been the construction of higher-level models from basic raw data especially in the area of language or speech recognition. and I remember reading on Andrew Ng's facebook post on deep speech: 

> Our Deep Speech system for speech recognition attains 16.5% error on Switchboard (Hub5'00), outperforming previous published results. We also focus on realistic noisy environments (speech in a noisy crowd, car, etc.) In this regime Deep Speech significantly outperforms commercial systems. Key to this approach were (i) Our scalable multi-GPU infrastructure for training an RNN, (ii) Using 7,000 hours of clean speech data, and using that to synthesize a massive 100,000 hours of data (by adding the clean data to different types of noise) to train the models. I think end-to-end deep learning is the future of speech.

In that spirit, here are two of my favourite papers from the conference. To see more, please visit the accepted papers [page](http://www.dlworkshop.org/accepted-papers)

* **Distilling the Knowledge in a Neural Network - Hinton, Vinyals and Dean** 

> Many insects have a larval form that is optimized for extracting energy and nutrients from the environment and a completely different adult form that is optimized for the very different requirements of traveling and reproduction. In large-scale machine learning, we typically use very similar models for the training stage and the deployment stage despite their very different requirements: For tasks like speech and object recognition, training must extract structure from very large, highly redundant datasets but it does not need to operate in real time and it can use a huge amount of computation. Deployment to a large number of users, however, has much more stringent requirements on latency and computational resources. The analogy with insects suggests that we should be willing to train very cumbersome models if that makes it easier to extract structure from the data. The cumbersome model could be an ensemble of separately trained models or a single very large model trained with a very strong regularizer such as dropout. Once the cumbersome model has been trained, we can then use a different kind of training, which we call “distillation” to transfer the knowledge from the cumbersome model to a small model that is more suitable for deployment. A version of this strategy has already been pioneered by Rich Caruana and his collaborators. In their important paper they demonstrate convincingly that the knowledge acquired by a large ensemble of models can be transferred to a single small model.


* **Deep Learning as an Opportunity in Virtual Screening**

> Deep learning excels in vision and speech applications where it pushed the stateof-the-art to a new level. However its impact on other fields remains to be shown. The Merck Kaggle challenge on chemical compound activity was won by Hinton’s group with deep networks. This indicates the high potential of deep learning in drug design and attracted the attention of big pharma. However, the unrealistically small scale of the Kaggle dataset does not allow to assess the value of deep learning in drug target prediction if applied to in-house data of pharmaceutical companies. Even a publicly available drug activity data base like ChEMBL is magnitudes larger than the Kaggle dataset. ChEMBL has 13 M compound descriptors, 1.3 M compounds, and 5 k drug targets, compared to the Kaggle dataset with 11 k descriptors, 164 k compounds, and 15 drug targets.
>
> On the ChEMBL database, we compared the performance of deep learning to seven target prediction methods, including two commercial predictors, three predictors deployed by pharma, and machine learning methods that we could scale to this dataset. Deep learning outperformed all other methods with respect to the area under ROC curve and was significantly better than all commercial products. Deep learning surpassed the threshold to make virtual compound screening possible and has the potential to become a standard tool in industrial drug design.

