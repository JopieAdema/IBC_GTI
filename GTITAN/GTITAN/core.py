import ast
import copy
import datetime
import glob
import json
import os
import pickle
import random
import shutil
import time
import warnings
import imp
from google_trans_new import google_translator
import networkx as nx
import numpy as np
import pandas as pd
from pytrends.request import TrendReq
from tqdm import tqdm
import gtab
from pytrends import exceptions
from functools import reduce


#TODOs for later:
class GTITAN:
    def __delete_all_internal_files(self):
        """  Deletes all saved caches (keywords, results and pairs). Be careful! """
        print("To be built")

    def __init__(self, dir_path=None,develop=True):
        """
        Initializes a GTITAN instance with the desired directory.
        :param dir_path:  path where to create a directory. If left to None, uses default package directory;
        """
        
        self.develop = develop
        if dir_path is None:
            #This queries 1 path up
            self.dir_path = os.path.dirname(os.path.abspath(__file__))
            if not os.path.exists(os.path.join(self.dir_path, "checkpath")):
                os.makedirs(os.path.join(self.dir_path, "checkpath"))
        else:
            #TODO: make all folders if new folder indicated: copy default files there such as the config.
            self.dir_path = dir_path
            if not os.path.exists(dir_path):
                default_path = os.path.dirname(os.path.abspath(__file__))
                # creating directory structure
                os.makedirs(os.path.join(self.dir_path, "config"))
                os.makedirs(os.path.join(self.dir_path, "data", "Translations"))
                os.makedirs(os.path.join(self.dir_path, "data", "Trend_indices"))

                # copying defaults
                shutil.copyfile(os.path.join(default_path, "config", "config_py.json"),
                                os.path.join(self.dir_path, "config", "config_py.json"))
            else:
                print("Directory already exists, loading data from it.")

        print(f"Using directory2 '{self.dir_path}'", __file__)
        with open(os.path.join(self.dir_path, "config", "config_py.json"), 'r') as fp:
                self.CONFIG = json.load(fp)

        #set configuring settings:
        self.CONFIG['CONN']['timeout'] = tuple(self.CONFIG['CONN']['timeout'])
        self.t_sleep = 0.2#also get it from 
        self.google_timeout = 14*60*60
        self.t_block = 0
        
        #Call instances of used packages
        self.translator = google_translator()  
        #self.pytrend = TrendReq(hl='en-US', **self.CONFIG['CONN'])
        self.pytrend = TrendReq()
        self.gtab = gtab.GTAB()
        
        # sets default anchorbank
        default_project = "frontex"
        self.set_active_project(default_project)
        
    def set_active_project(self, default_project):
        """
            Sets the  for querying in the online phase.
            Input parameters:
                default_queries - filename of the desired project. N.B. must exist in 'output/google_anchorbanks'
        """

        #print(f"Active anchorbank changed to: {os.path.basename(self.active_gtab)}\n")

    def _anchor_list(self):
        anch_list=[]
        anch_loc = os.path.join(self.dir_path, "output", 'google_anchorbanks')
        for f in glob.glob(os.path.join(anch_loc,'*')):
            anch_list.append(f.replace(anch_loc,""))
        return anch_list

    def _build_single_anchorbank(self,iso2_code, time_frame = "today 5-y", category = '0'):
        self.gtab.set_options(gtab_config = {"num_anchor_candidates": 200, "num_anchors": 50, "sleep": 0.2})
        self.gtab.set_options(pytrends_config={"geo": iso2_code, "timeframe": time_frame, "cat": category})
        try:
            #TODO: Fork GTAB and make sure it raises a catchable error here, as it does with the normal sourcing!
            self.gtab.create_anchorbank()
            status = 1
        except:
            print("IP limit reached")
            self._set_sleep('61')
            status = 0
        return status
    
    def build_all_anchorbanks(self,origin_list, cat_list, time_frame = "all"):
        anch_list=self._anchor_list()
        for c in cat_list:
            for i in origin_list:
                anchor_name = 'google_anchorbank_geo='+i+'_cat='+c+'_timeframe='+time_frame+'.tsv'
                if anchor_name in anch_list:
                    print('Anchor pre-existing, skip!')
                else:
                    print('Build ',anchor_name )
                    status = self._build_single_anchorbank(i, time_frame, c)
                    print(status)
                    anch_list.append(anchor_name)
                    
   
    def _set_sleep(self,sleep_time):
        print("Sleep time between queries set to",sleep_time)
        self.gtab.set_options(gtab_config = {"num_anchor_candidates": 200, "num_anchors": 50, "sleep": sleep_time})
        self.t_sleep = float(sleep_time)
        if self.t_sleep>60:
            self.t_block = time.time()

    def _set_anchors(self,anchor_candidates,anchor_number):
        self.gtab.set_options(gtab_config = {"num_anchor_candidates": anchor_candidates, "num_anchors": anchor_number})
    def _show_anchorbanks(self):
        self.gtab.list_gtabs()
    def _time_reset_checker(self):
        if time.time()>self.t_block+self.google_timeout:
            print("14 hours have passed since the last IP block, we try again to set ")
            self._set_sleep('0.2')

    def transLangTerm(self,l_list=[['Arabic','ar']],tr_list=["Hello"]):
        #NOTE: Look how to save in the folder DATA->Trranslatioons
        if ('df_tr' in locals()) & (self.newdf==False):
            print("There is already a frame in use!")
        else:
            try:
                if self.newdf==True:
                    raise NewError('Load a new DF')
                df_tr = pd.read_csv('translations.csv')
                print("Frame loaded!")
            except:
                column_names=['keys','Language',"Translation"]
                df_tr = pd.DataFrame(columns=column_names)
                print("New frame initialized!")
        for tr in tr_list:
            for l in l_list:
                if ((df_tr['keys'] == tr) & (df_tr['Language'] == l[0])).any()==False:
                    try:
                        translated_text = self.translator.translate(tr,lang_src='en',lang_tgt=l[1])
                    except:
                        if self.raise_IP==True:
                            if "response" in dir(e):
                                if e.response.status_code == 429:
                                    input("Google Translate Quota reached! Please change IP and press any key to continue.")
                                    translated_text = self.translator.translate(tr,lang_src='en',lang_tgt=l[1])
                                    
                                else:
                                    print("Unknown error")
                                    
                    print(tr," in ",l[0], 'is: ',translated_text)
                    slice_df = pd.DataFrame({'keys':[tr],
                                                 'Language':[l[0]],
                                                 'Translation':[translated_text]})
                    df_tr = df_tr.append(slice_df)
                    time.sleep(0.2)
                else:
                    print('We have already translated this term')
        df_tr.to_csv('translations.csv')
        return df_tr
                        
    def _run_single_pytrends(self,key,timeframe,geo,cat,gprop):
        time.sleep(self.t_sleep)
        try:
            self.pytrend.build_payload(key, timeframe = timeframe, geo=geo, cat = cat, gprop = gprop)
        except ConnectionError:
            print('We do not have an internet connection')
            time.sleep(100)
            try:
                self.pytrend.build_payload(key, timeframe = timeframe, geo=geo, cat = cat, gprop = gprop)
            except:
                input("Internet connection dropped! Please reconnect and press any key to continue.")
                self.pytrend.build_payload(key, timeframe = timeframe, geo=geo, cat = cat, gprop = gprop)
        except Exception as e:
            if self.raise_IP==True:
                if "response" in dir(e):
                    print(e)
                    if e.response.status_code == 429:
                        input("GTI Quota reached! Please change IP and press any key to continue.")
                        self.pytrend.build_payload(key, timeframe = timeframe, geo=geo, cat = cat, gprop = gprop)
                    else:
                         print("Unknown error")
            else:
                print('We swap to 61 seconds waiting time')
                print(key,timeframe,geo,cat,gprop)
                self._set_sleep('61')
                time.sleep(self.t_sleep)
                self.pytrend.build_payload(key, timeframe = timeframe, geo=geo, cat = cat, gprop = gprop)
        pytrend_obj = self.pytrend
        return pytrend_obj

    def run_all_keys_pytrends(self, key_list, timeframe= 'all', geo='NL', cat='0', gprop=''):
        #region_list = pd.DataFrame()
        #TODO: catch 400 error!
        #Because of the wrapper run_pytrends_df we only query same terms in a different language together
        key_list=list(set(key_list))
        key_iter = [key_list[i:i + 5] for i in range(0, len(key_list), 5)]
        for key in key_iter:
            pytrend_obj = self._run_single_pytrends(key,timeframe,geo,cat,gprop)
            try: 
                trend_list = trend_list.join(pytrend_obj.interest_over_time().drop(columns='isPartial'))
                #region_list = region_list.join(pytrend_obj.interest_by_region())
            except:
                trend_list = pytrend_obj.interest_over_time()
                #region_list = pytrend_obj.interest_by_region()#we can only do this for within a country
        return trend_list#, region_list
        
    def run_pytrends_df(self, src_df):
        src_dfs = [x for _, x in src_df.groupby(['timeframe','geo','cat','gprop'])]#,'keys'
        trend_all_list = []
        #region_all_list= []
        for i in src_dfs:
            timeframe = i['timeframe'].unique()[0]
            geo = i['geo'].unique()[0]
            cat = i['cat'].unique()[0]
            gprop = i['gprop'].unique()[0]
            trend_part_list=[]
            #region_part_list = []
            src_dfs2 = [x for _, x in i.groupby(['timeframe','geo','cat','gprop','keys'])]
            for j in src_dfs2:
                
                trend_list = self.run_all_keys_pytrends(list(j['key']), timeframe=timeframe ,geo=geo, cat=cat,gprop=gprop)
                trend_list['cat']=cat; trend_list['geo']=geo; trend_list['gprop']=gprop; #region_list['cat']=cat; region_list['geo']=geo; region_list['gprop']=gprop
                cols_to_sum = j['key'].unique() 
                try:
                    trend_list[j['keys'].unique()[0]] = trend_list[cols_to_sum].sum(axis=1)
                    trend_list.drop(columns=cols_to_sum, inplace=True)
                except KeyError:
                    print("The DF is empty: no match found. We create an empty DF as a placeholder with same dimensions.")
                    #query English term in USA and set the values to 0:
                    trend_list = self.run_all_keys_pytrends(list(j['key']), timeframe=timeframe ,geo="US", cat="0",gprop='')
                    trend_list['cat']=cat; trend_list['geo']=geo; trend_list['gprop']=gprop; #region_list['cat']=cat; region_list['geo']=geo; region_list['gprop']=gprop
                    cols_to_drop = j['key'].unique()
                    
                    trend_list[j['keys'].unique()[0]] = 0
                    print('cols_to_drop: ',cols_to_drop,"columns of trendlist:",list(trend_list.columns))
                    trend_list.drop(columns=cols_to_drop, inplace=True)

                trend_part_list.append(trend_list)
                #region_part_list.append(region_list)
                
            trend_all_list.append(trend_part_list)
            #region_all_list.append(region_all_list)
            #TODO: region all list is not working properly
        return trend_all_list#,region_all_list
        
    def main_single_list(self,src_df,anchorbanking):
        """
        Runs GTITAN sing a single data format "src_df"  of N (number of search queries) with the following columns:
        
        :param src: List of keywords with  ;
        :bool anchorbanking: Whether to anchorbank or not. An advantage of not anchorbanking is the availability of ;
        """
        if anchorbanking==False:
            print("We are going to use pytrends directly")
            trend_all_list = self.run_pytrends_df(src_df) 
            instance_list=[]
            for i in trend_all_list:
 
                j = reduce(lambda  left,right: pd.merge(left.drop(columns=('isPartial')),right.drop(columns=['geo','cat','gprop']),how='outer',left_index=True, right_index=True), i)
                instance_list.append(j)

            trend_all_list = pd.concat(instance_list).drop(columns='isPartial')#ignore_index=True
            
        else:
            print("We are going to fetch an anchorbank using GTAB: Not Yet Implemented")
            
        return trend_all_list#,region_all_list
    
    def main_flex(self,trans_dict,roi_df,gprop_df,key_df,cat_df,timeframe_df,
                  translate=True,anchorbanking=False,raise_IP=False,proxy_list = [],baselang_tuple=['English','en'],newdf=False):
        
        self.raise_IP = raise_IP
        self.anchorbanking=anchorbanking
        self.newdf = newdf
        
        roi_df['lang_tuple']=''
        for index, row in roi_df.iterrows():
            row['lang_tuple'] = trans_dict[row['regions']] 
            if (baselang_tuple in row['lang_tuple']): 
                print ("Contains English already")
            else:
                row['lang_tuple'].append(baselang_tuple)
        df = roi_df.explode('lang_tuple')
        df['tmp'] = 1; key_df['tmp'] = 1; gprop_df['tmp'] = 1; cat_df['tmp'] = 1; timeframe_df['tmp'] = 1
        #merge
        dfa = df.merge(key_df, on=['tmp']).merge(gprop_df, on=['tmp']).merge(cat_df, on=['tmp']).merge(timeframe_df, on=['tmp']).drop(columns='tmp')
        
        #TODO: make a translate==False switch
        if translate==True:
            dfa['Language'] = dfa["lang_tuple"].str[0]
            df_translation = dfa[['lang_tuple','Language']]
            df_languages = df_translation.drop_duplicates(subset=['Language'])
            l_list = list(df_languages['lang_tuple'])
            tr_list = list(set(list(key_df['keys'])))
            trans_df = self.transLangTerm(l_list=l_list,tr_list=tr_list)

            dfa = dfa.merge(trans_df, on=['Language','keys'])
            dfa = dfa.rename(columns={'regions': 'geo', 'Translation': 'key'}).drop(columns=['lang_tuple'])
        #problem: we can't sum translated queries if they dont go together into pytrends: we should fix this
        result = self.main_single_list(dfa,False)
        return result
        
    def main_flexible(self,src_list,src_list_type,cat_list,trans_list, timeframe, translate=False,anchorbanking=False,raise_IP=False,proxy_list = []):
        #TODO: is this function of any use still??
        """
        Runs GTITAN 
        
        :param src_list: List of keywords with  ;
        :param src_list_type: 
        :param cat_list:
        :param src_list_type:
        :param trans_list: List of languages
        :bool translate: Whether to translate
        :bool anchorbanking: Whether to anchorbank or not. An advantage of not anchorbanking is the availability of ;
        :param proxy_list: List of proxies to use to query Google. If empty, 
        """
        self.raise_IP = raise_IP
        self.anchorbanking=anchorbanking
        
        srcarray = numpy.array(srclist)
        self.srcar = srcarray
        self.srclisttype = srclisttype
        self.cat_length = len(catlist)
        if srclisttype=="Cross":
            print("OK")
        if len(self.srcar.shape[1])!=2:
            raise ValueError("Incorrect input dimensions")
        self.key_length=self.srcar.shape[0]
        if translate==True:
            print("We are going to translate search terms")
        #Set sleep
        if proxy_list==[]:
            self._set_sleep(self,'61')
                 
        
        if anchorbanking==True:
            self._build_all_anchorbanks()

        #also make a counter that 14 hours after setting sleep to 60, we set sleep back to 0.2
        else: 
            print("We will use standard pytrends!")
            #maybe we can use GTABs 429-catcher
            
            
        #now we use the main function for nicely formatted functions:
        #self.main_single_list(src_df,anchorbanking)
