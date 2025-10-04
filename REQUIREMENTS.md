# LOOP-EXTRACTOR
## Introduction
In High-Performance Computing (HPC) and Heterogenous Computing (HC) there are a many underlying maxims and among them is the need to:
* Expose parallelism and exploit it
* Work with the systems memory architecture to maximize memory bandwidth
  
When looking at an existing code-base with the intent of applying these two maxims attention is often drawn to loops.  

Loop structures can be very complex and can often span multiple source files when you consider the content of those loops. 

Often loops can also be very subtle and not be coded in easily recognizable standard loop structures, this is a class of loops that is left to future work.

So while we can visually scan source code or can use `grep` tools to find standard loop structures there remains the challenge of collecting information about loops at scale to understand the potential that loops offer for optimization.

Any effort to better understand loops needs to go through these stages:
* Individual Loop Structure and Location
  * Location in the source code - File path, function or method 
  * Scope of the loop in the source code - Line numbers for begin and end of the loop
  * Loop bounds - How is the loops index initialized, under what conditions should it operate, how is the loop index updated.
* Loop Nesting
  * Loops within loops - Any data about loops needs to consider that loops themselves can contain other loops. This nesting can be simple but often it can be complex.
  * Functions within loops - Often because of the complexity of looping structures software designer and developers will use methods and functions to modularize the code and thereby hide the complexity. So the relationship of loops and functions of methods they will call is important to understand.
* Loop Content
  * Operations - Loops alone don't tell the story of the compute they contain. Knowing the operations and characterizing them into sub classes can help to guide loop and performance optimization work.
  * Memory access patterns - Often the most intense work in performance optimization is adjusting/refactoring loops to increase data locality both for cache optimization and also when positioning data for use in accelerators. Understand the flow of data consumed and created in a loop is important to the performance optimization.

## Goal
The goal of this tool is to make the understanding of loops as mentioned above easier by creating a tool that can be used to scan existing C++/C code bases. 

## Order of Solve/Design
To create this tool we will go in stages:
1. Data Collection: Using python and clang create a source code scanner that can collect the and store the data necessary for later analysis and because we expect that new information will be necessary that the tool should be built in a way that makes it easy to extend and these extensions shouldn't effect downstream analysis.
   1. Given a path the tool should traverse the path looking for and scanning source code.
   2. Extract information using clang AST based utilities that look for the information to support the items above in the introduction 
   3. Encode the the data into a data-model that is source code file based, respects function, method, and class. And properly lays out the data objects so that new analysis can be included easily in a manner that doesn't interfere with downstream analysis.
   4. Store data/information collected in a JSON file.
2. Analysis: This topic will be addressed later and should be ignored for now.

