import numpy as np
import itertools
import math
import pandas as pd

from itertools import groupby
from scipy.stats.stats import pearsonr

import sys
import fasta_reader
import matplotlib
#matplotlib.use('agg')
import seaborn as sns
import matplotlib.pyplot as plt
import os
import multiprocessing

import collections

'''
@Author: Daniel Sprague
@Lab: Calabrese Lab
@Department: Department of Pharmacology, University of North Carolina at Chapel Hill

Python 3.7
Anaconda Distribution

'''

'''

# ``````````````````````````````````````````````````````````````````````````````
# This library of functions performs all necessary operations for k-mer
# analysis of RNA/DNA

# Members:
# count_kmers, target_norm, kmer_pearson, tile_seq, make_plot
# dseekr, global_tile_seq (now redundant), global_kmer_pearson (now redundant)
# global_stats


# ``````````````````````````````````````````````````````````````````````````````
'''

'''
# This function counts length normalized kmers per kb

# Input:
#   1. DNA sequence (str)
#   2. Value of k (int)
#   3. Dictionary of kmers (OrderedDict)

# Output:
#   1. Array of kmers for sequence (ndarray)
'''

def count_kmers(fa,k,d,norm=True):
    currlen = len(fa)
    vals = np.zeros(len(d))
    for i in range(currlen-k+1):
        if fa[i:i+k] in d:
            vals[d[fa[i:i+k]]]+=1
    if norm:
        vals = 1000*(vals/currlen)
    return vals
'''
# This function normalizes kmer counts relative to the
# mm10 gencode lncrna reference for a DNA sequence
# or list of sequences

# Dependencies:
#   1. kmerprofilelib.count_kmers

# Input:
#   1. reference array of kmer counts (ndarray)
#   2. target sequence (string or list of strings)
#   3. kmer value (int)

# Output:
#   1. Normalized kmer counts (ndarray)
'''
def target_norm(ref,target,k):
    means,sd = np.mean(ref,axis=0),np.std(ref,axis=0)
    pos,bases = 4**k,['A','T','C','G']
    keys = [''.join(p) for p in itertools.product(bases,repeat=k)]
    d = collections.OrderedDict(zip(keys,range(0,pos)))
    if len(target) == 1:
        tilenorms = np.zeros(pos)
        target_kmer_count = count_kmers(target[0].upper(),k,d.copy())
        target_kmer_count_norm = (target_kmer_count-means)/sd
        tilenorms = target_kmer_count_norm
    else:
        tilenorms = np.zeros((len(target),pos))
        j = 0
        for seq in target:
            target_kmer_count = count_kmers(seq.upper(),k,d.copy())
            target_kmer_count_norm = (target_kmer_count-means)/sd
            tilenorms[j] = target_kmer_count_norm
            j+=1
    return tilenorms
'''
# This function calculates the pearson correlation
# coefficient between two "kmer arrays"

# Input:
#   1. Query normalized kmers (ndarray size 1x4^k)
#   2. Target normalized kmers (ndarray size num_tilesx4^k)

# Output
#   1. One dimensional array of pearson r values (ndarray)
#      of length 4^k
'''
def kmer_pearson(query,target):
    target,query = pd.DataFrame(target).T, pd.Series(query)
    return target.corrwith(query)
    # R,i = np.zeros(len(target)),0
    # R[R==0] = np.nan
    # for row in target:
    #     R[i] = pearsonr(query,row)[0]
    #     i+=1
    # return R

''' tile_seq

opens a fasta file and returns a list of strings containing tiles of length L and interval s

input: path-like string, int length of tile, int interval
output: list of strings

'''

def tile_seq(fa,length,skip):
    fa = fa.upper()
    tiles = [fa[i:i+length] for i in range(0,len(fa),skip)]
    return tiles




'''

This function fragments a DNA sequence into overlapping tiles, and then performs
SEEKR against a set of query sequences that are known to represent some biological
function/phenomena (for example, the tandem repeats of Xist ). The output is a
score representing how similar a transcript is to Xist.

This function is called by the partial() function in a launching script using
the multiprocessing module

This function is going to be split and implemented into a more abstracted structure
in future development and combined with the dseekr function above.
'''
def global_stats(sd,l,s,plot_dict,lncref,queryfiles,plotrefs,lncrnas,out,k):
    queryfiles_kmers = dict([(i,v) for i,v in queryfiles.items() if f'{k}mer' in i])
    lncref_kmers = [v for i,v in lncref.items() if f'{k}mer' in i]


    reader = fasta_reader.Reader(lncrnas)
    seqs = reader.get_seqs()

    queryfiles_kmers = dict(sorted(queryfiles_kmers.items()))

    counts = np.zeros((len(seqs),len(queryfiles_kmers)))

    #MAKE ASSIGNMENT OF QUERY TO ARRAY INDEX EXPLICIT
    #USING DICT

    queryids = dict(zip(list(queryfiles_kmers),range(len(queryfiles_kmers))))

    for i,seq in enumerate(seqs):
        curr_tile_fa = tile_seq(seq,l,s)
        curr_normcount = target_norm(lncref_kmers[0],curr_tile_fa,k)

        for query in queryfiles_kmers:
            lncomedata = plotrefs[query]
            thresh = np.mean(lncomedata)+np.std(lncomedata)*sd
            curr_q = queryfiles_kmers[query]
            R = kmer_pearson(curr_q,curr_normcount)
            sig_hits = len(R[R>thresh])
            counts[i][queryids[query]] = sig_hits/len(curr_tile_fa)

    np.savetxt(f'./{out}_{k}mers_{sd}sd.csv',counts,delimiter=',')
    return
