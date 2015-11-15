# Product Review Analyzer


1. [Overview][]
2. [Components][]
3. [Caution][]


## Overview

This program analyzes opinions from product reviews using partially supervised learning technics. Hence the whole process(especially training and tuning steps) can be done almost without human efforts.


### The Process

The process consists of 2 steps:

1. [Labeling Sentiments][]
2. [Extracting Opinions][]


#### Labeling Sentiments

The first step of analysis is labeling sentiments using [Sentiment Analyzer][]. The analyzer labels each word with sentiment predicted using [Conditional Random Field][] and [Word2Vec][].

For example:

> 가격도 저렴해요. 그리고 충전 속도도 매우 빠르네요.  
> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+&nbsp;

#### Extracting Opinions

Next step of the process is extracting opinions. Because the most important thing can be found in the reveiw is opinions about features of the product, the program uses [Opinion Extractor][] to extract opinions about features which have labeled sentiments.

For example:

> 가격도 저렴해요. 그리고 충전 속도도 매우 빠르네요.  
> - "가격도 저렴해요"  
> - "충전 속도도 매우 빠르네요"


## Components

1. [Sentiment Analyzer][]
2. [Opinion Extractor][]
3. [Product Recommender][]


### Sentiment Analyzer

It predicts sentiment using trained [Conditional Random Field] model. The training is done almost fully automatically:

The program uses [Word2Vec][] to construct dictionaries for each sentiment poles based on few "seed words" which manually selected, and label each words with algorithm similar to [K Nearest Neighbors][] with [Chebyshev Metric][]. Then train the [Conditional Random Field][] model using them.


### Opinion Extractor

The program uses simple patterns to find candidates for opinion, then apply [Affinity Propagation][] clustering algorithm on vectorized words(using [Word2Vec][]). Then each cluster is classified as opinion and non-opinion by some scoring metric like frequency and occurring contexts. This process works without any human works.

### Product Recommender

Based on the results of analysis of products in each category, the program can make recommendations.


## Caution

The project is **just a proof of concept.**, and some libraries like morpheme analyzer and trained models are **not included** for now. If you want to try out, then you can use open-source projects like Mecab-ko.



[Overview]: #overview
[Labeling Sentiments]: #labeling-sentiments
[Extracting Opinions]: #extracting-opinions

[Components]: #components
[Sentiment Analyzer]: #sentiment-analyzer
[Opinion Extractor]: #opinion-extractor
[Product Recommender]: #product-recommender

[Caution]: #caution

[Word2Vec]: https://code.google.com/p/word2vec/
[Conditional Random Field]: https://en.wikipedia.org/wiki/Conditional_random_field
[K Nearest Neighbors]: https://en.wikipedia.org/wiki/K-nearest_neighbors_algorithm
[Chebyshev Metric]: https://en.wikipedia.org/wiki/Chebyshev_distance
[Affinity Propagation]: https://en.wikipedia.org/wiki/Affinity_propagation
