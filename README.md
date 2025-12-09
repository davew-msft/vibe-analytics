# Vibe Analytics:  Advancing Self-Service Analytics

<p align="center">
  <img src="./img/va.png" alt="Vibe Analytics">
</p>

Era of AI Day 
Thursday December 11, 2025  
Microsoft's Philadelphia Innovation Hub  

[See also:  nl2sql](https://github.com/davew-msft/nl2sql)  

## What is this?  Why are we here?

While "[Natural Language to SQL](https://github.com/davew-msft/nl2sql)" is great, we want to take this to the NEXT LEVEL.

_Vibe analytics_ builds on **vibe coding**, which is an informal, intuition-driven way of programming where you write code by "feeling out" the solution rather than following a strict plan. 

>As a business person, I want to be able to have conversations with my data _on my terms_.  I don't just need help writing SQL, I need help thinking through the entire _analytics process_.  I want the AI to help me find _nuggets of gold_ in my data and help me make good, data-driven decisions.  

So, what is the _analytics process_?  What should anyone (data scientists, data engineers, business analysts) understand when they are working with data?  

>The best data scientists have a process they follow to understand the data better so it can help them unlock value. What we attempt to do during this session is show you how I do it, but leveraging as little coding experience as possible.  Can an LLM do this for us?   

## _The Analytics Process_

I follow a process that the industry calls _Exploratory Data Analytics_.  EDA involves manually exploring, visualizing, and summarizing data to understand its various aspects. The goal would be to do this when you don't understand the data or want to ensure you aren't injecting your _biases_ and _preconceived notions_ into the data. LLMs can really help here. Most folks, even data scientists, even me, really struggle with EDA. You have to follow a process. LLMs and vibe coding can help you adhere to a good framework for doing this.

It helps in identifying patterns, detecting inconsistencies, testing assumptions, and gaining insights.

EDA also involves:  
  * data cleaning (it seems like our data is never perfect)
  * handling missing values
  * outlier detection 

This work is cumbersome and error-prone, even for the best data scientists and engineers. LLMs to the rescue!


## What do I need to get started?

Right now...this works best using:  

* vscode
* Fabric (which has MCPs for vscode to assist with Vibe Analytics).  
  * **You do not need Fabric Copilot**
  * You can setup a Fabric workspace inexpensively for testing/personal work
* Spark notebooks/Jupyter notebooks
  * these work best because they have the ability to display visualizations, can connect to various data sources, etc

**While this is likely NOT IDEAL for business people to do analytics, it is not difficult to set these things up and it gives you the most flexibility**.  If you are interested, at the Microsoft Innovation Hub, we do additional sessions where we can show you have to set all of this up so the business user can simply use a browser to accomplish these tasks.  

[How to Setup Your Environment](./env-setup.md)

## Demo with CRIT prompts

Let's look at some demos to show you the _Art of the Possible_.  

* [Here's an End-to-End Demo Using CRIT prompting and Guided Analytics techniques](./GuidedAnalytics/README.md)
  * We'll look at _Guided Analytics_ (which is just another term for EDA)
  * CRIT prompting
  * using Microsoft Fabric for Vibe Analytics (Guided Analytics)

## Demo:  Can the LLM spot the problem with our data and recommend prescriptive actions?  

  Even more importantly, can you figure it out?  

  [Follow along in this Fabric Spark notebook](./CognitiveMistakes.ipynb)



