# -*- coding: utf-8 -*-
"""deviceparser

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nJuRGlXvCWjgxv-qTCSLM4NOTJNIbs0a
"""
import json 
import re
import numpy as np
import pandas as pd

class ParsingFunctions:
  '''A class for housing all the parsing function which will be used on device specs data'''
  
  # a list to keep track of which features have parsing functions
  allow_parsing = []
  # a set to keep track of parsed features
  parsed_features = set()
  
  def parse_spec(self, spec_, value):
    '''A function for parsing each of the spec to get the information we want
       This function is meant to be called on each iteration of banner_spec/value pair
    '''
    # check if spec_ is the in the allow_parsing list
    if spec_ in ParsingFunctions.allow_parsing:
      # parsing function for a feature MUST be stored as a function of the name, parse_feature_name
      # for example, parse_banner_batsize_hl is the parsing function for the feature banner_batsize_hl
      parsing_function_name = 'parse_' + spec_
      parsing_function = getattr(ParsingFunctions, parsing_function_name)
      parsed_values = parsing_function(value)
      # parsing functions will be written in such a way that the features and values are part of a dict
      for feature_name, feature_value in parsed_values.items():
        setattr(self, feature_name, feature_value)
        self.set_all_features(feature_name)
        self.create_feature(feature_name)
        ParsingFunctions.add_to_parsed_features(feature_name)
    # if spec_ in not in the allow_parsing list, simply set the value current value of the spec
    else:
      setattr(self, spec_, value)
      self.set_all_features(spec_)
      self.create_feature(spec_)
      
  @classmethod   
  def add_new_parsers(cls, new_parsers):
    '''A function for creating user defined parsers, initiliaze new parsers before calling Device
    
       Accepts a single function or a list of functions   
    '''
    # if a list of parsers is provided, check if each parser is a function that follows our name format
    if isinstance(new_parsers, list):
      for n, parser in enumerate(new_parsers):
        if not callable(parser):
          raise TypeError('parser at index {} in new_parsers must be callable, not of type {}'.format(n, type(parser)))
        else:
          parsing_function_name = parser.__name__
          # slice the name, say parse_batsize_hl at parse_  i.e [6:]
          col_name = parsing_function_name[6:]
          if col_name not in cls.allow_parsing:
            cls.allow_parsing.append(col_name)
            setattr(cls, parsing_function_name, parser)
          else:
            print('WARNING! function for parsing {} already exists! {} was not added'.format(col_name, parsing_function_name))
    elif callable(new_parsers):
      parsing_function_name = new_parsers.__name__
      col_name = parsing_function_name[6:]
      if col_name not in cls.allow_parsing:
        cls.allow_parsing.append(col_name)
        setattr(cls, parsing_function_name, new_parsers)
      else:
        print('WARNING! function for parsing {} already exists! {} was not added'.format(col_name, parsing_function_name))
    else:
      raise TypeError('parser must be callable, not of type {}'.format(type(new_parsers)))
    
  @classmethod
  def clear_existing_parsers(cls):
    '''A function for clearing current parsers'''
    cls.allow_parsing = []
    print('All exisiting parsing functions have been cleared!')
    
  @classmethod
  def add_to_parsed_features(cls, feature_name):
    '''A function for keeping track of which features were parsed'''
    cls.parsed_features.add(feature_name)
    

class FeatureGen(ParsingFunctions):
  '''FeatureGen will contain a dict of all features from all the devices called all_features_dict
  
     It also contains a collection of useful methods for parsing data from a Devices object
  '''
  
  # initialize a collector dictionary to collect features from all devices
  # out dict will have a feature called device_notes for collecting specs where the key is nan
  all_features_dict = {'device_notes':None}
  
  def gen_from_dict(self, spec_value, spec_name):
    '''A fnction for generating more features from the value of a spec if the spec_value is also a dict'''
    for key, value in spec_value.items():
      if pd.isna(key):
        key = 'nan'
      if pd.isna(value):
        value = 'nan'
      key_ = self.split_string(key)
      # in some cases, the spec_ is NaN or '' and in other case the value is nan or ''
      # account for these cases 
      # don't take any action, this is a waste attribute, we don't want to add it to the feature list of a device
      if (key_ == 'nan' or key_ == '') and (value == '' or value == 'nan'):
        pass
      # if key is 'NaN' or '', but the value is not, we want to create a note about the value under device_notes
      elif (key_ == 'nan' or key_ == '') and (value != '' or value != 'nan'):
        # create a new note using the key and value which is of the format 'battery_-This device has great battery life'
        self.device_notes.setdefault(spec_name, value)
      # if the key is not empty and the value is, we do not want this spec
      elif (key_ != 'nan' or key_ != '') and (value == '' or value == 'nan'):
        pass
      # if none of the above issues are there, we can add the feature as an attribute of the device
      else:
        new_key = spec_name + '_' + key_
        self.parse_spec(new_key, value)
        

class Device(FeatureGen):
  '''A class for working with device data scrapped on GSMArena''' 
  # we want to initalize a list to keep track of all the features collected for THIS device
  features_list = []
   
  # initliaze the class using a device 
  def __init__(self, device, device_id, maker_name, maker_id):
    # start adding attributes to the device object  
    self.maker_name = maker_name
    self.create_feature('maker_name')
    self.set_all_features('maker_name')
    
    self.maker_id = maker_id
    self.create_feature('maker_id')
    self.set_all_features('maker_id')
    
    self.device_id = device_id
    self.create_feature('device_id')
    self.set_all_features('device_id')
                
    # set the device_info as attributes of the Device 
    for device_info_name, device_info in device.items():
      # emulates the functionality of self.varable = value
      setattr(self, device_info_name, device_info)
      self.create_feature(device_info_name)
      self.set_all_features(device_info_name)
    
    # all device "specs" exception opinion are a dict of sub specs, which we need to parse
    # these will be treated separetly using FeatureGen and ParsingFunctions
    self.device_notes = {}
    for spec, value in device['device_specs'].items():
      spec_ = self.split_string(spec)
      if isinstance(value, dict):
        self.gen_from_dict(value, spec_)
        self.create_feature(spec_)
      else:
        setattr(self, spec_, value)
      
      
  def split_string(self, spec_name):
    '''A function for changing the ' ' and '-' demlimiter
       in a spec_name to  '_'
       
       Given 'Selfie Camera', returns selfie_camera
    '''
    split_spec_pattern = re.compile('\s|-|–')
    split_specs = re.split(split_spec_pattern, spec_name)
    return '_'.join(split_specs).lower()
  
  
  def create_feature(self, spec_name):
    '''A function that allows us to consolidate the names of all features recovered from the GIVEN device'''
    if spec_name not in self.features_list:
      self.features_list.append(spec_name)
      
      
  def set_all_features(self, spec_name):
    '''A function that allows us to consolidate the names of all features recovered from ALL devices'''
    if spec_name not in FeatureGen.all_features_dict:
      FeatureGen.all_features_dict.setdefault(spec_name, None)
      
  
  @staticmethod
  def read_devices_json(file_path):
    '''A function for reading in a JSON file.

       Takes in the string file_path and returns a dict
    '''
    with open(file_path, 'r', encoding='utf-8') as file:
      devices_dict = json.load(file)
      return devices_dict
    
    
  @staticmethod
  def list_makers(devices_dict):
    '''A function that takes in the loaded devices_dict data and returns a list of makers
     
       Returns a list of the form  [(0, 'Acer'), .......] for all makers in the devices_dict
    '''
    makers = [(x, y) for x, y in zip(range(devices_dict.keys().__len__()), devices_dict.keys())]
    return makers
    
    
  @staticmethod
  def create_devices_from_data(devices_dict):
    '''A function for creating objects out of all the devices stored in devices_dict

       Retuns a list of Device objects for all devices in the devices_dict 
    '''
    # we want to initalize a list for collecting all the device objects
    devices_collector = []
    # each maker has a maker_id starting from 0 for all the makers
    for maker_id, (maker_name, devices_info) in zip(range(len(devices_dict.keys())), devices_dict.items()):
      maker_name_split = [split.upper() for split in re.split(re.compile(' |-'), maker_name)]
      maker_name_ = ''.join(maker_name_split)

      # iterate through each device under a maker and use maker_name_ and device_num to create a unique device_id
      for device_num, device in devices_info.items():
        device_id = maker_name_ + '_' + device_num
        # create the device object using the Device class and then append the object to the collector array 
        device_ = Device(device, device_id, maker_name, maker_id)
        devices_collector.append(device_)
    return devices_collector
        
  @staticmethod     
  def create_feature_column(feature_name, devices_collector):
    '''A function for creating a feature column of a given name using devices_collector'''  
    collector_array = []
    for device in devices_collector:
      feature = getattr(device, feature_name, None)
      if not feature:
        collector_array.append(np.NaN)
      else:
        collector_array.append(feature)
    return collector_array

        
  def create_df(devices_dict):
    '''A function for creating a DataFrame using all the data from all the Device objects'''
    
    if not devices_dict:
      raise AttributeError('This function cannot be run of devices_dict if is empty')
    
    # create Device objects from devices_dict
    devices_collector = Device.create_devices_from_data(devices_dict)
    print(devices_collector.__len__())

    # get a dict of all features collected across all devices
    all_features_dict = FeatureGen.all_features_dict

    # create the feature columns for each feature and set it as the new value of the all_features_dict
    for feature_name, _ in all_features_dict.items():
      col = Device.create_feature_column(feature_name, devices_collector)
      all_features_dict[feature_name] = col

    # create a DataFrame from the dict and return it
    return pd.DataFrame(all_features_dict)