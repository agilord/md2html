#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml, pystache;
import json, os, sys;

config = {};

# load config files
for i in range(1, len(sys.argv)):
    configFile = sys.argv[i];
    if configFile.endswith('.json'):
        with open(configFile) as data_file:    
            jmap = json.load(data_file);
            for k in jmap:
                config[k] = jmap[k];
    if configFile.endswith('.yaml'):
        with open(configFile) as data_file:
            ymap = yaml.load(data_file);
            for k in ymap:
                config[k] = ymap[k];

# create out dir
outputBase = config['output-dir'] + config['archive-url'];
if not (os.path.exists(outputBase)):
    os.mkdir(outputBase);

# archive db
dbtime = os.path.getmtime(config['archive-json']);
with (open(config['archive-json'], 'r')) as f:
    db = json.load(f);

def write_content(file, content):
    oldContent = '';
    if os.path.exists(file):
        with (open(file, 'rb')) as f:
            oldContent = f.read().decode('utf-8');
    if oldContent != content:
        print('Writing: ' + file);
        with open(file, 'wb') as f:
            f.write(content.encode('utf-8'));

def process_template(config, templateKey, resultPath):
    with (open(config[templateKey], 'r')) as f:
        mustacheText = f.read();
    newContent = pystache.render(mustacheText, config);
    if resultPath == None:
        return newContent;
    outFile = outputBase + resultPath;
    write_content(outFile, newContent);

allentries = [];
pubentries = [];
for v in db.values():
    if ('draft' in v) and (v['draft'] == True):
        continue;
    if (not 'summary' in v) and ('description' in v):
        v['summary'] = v['description'];
    allentries.append(v);
    if 'published' in v:
        pubentries.append(v);
        v['year'] = v['published'][0:4];
        v['year_mon_day'] = v['published'][0:10];
        v['mon_day'] = v['published'][5:10];
allentries.sort(key=lambda k: k['url']);
pubentries.sort(key=lambda k: k['published'], reverse=True);

# sitemap.xml
config['entries'] = allentries; 
process_template(config, 'sitemap-xml-template', 'sitemap.xml');

# ONLY PUBLISHED entries from here
if len(pubentries) == 0:
    exit(0);

# archive/atom.xml
config['entries'] = pubentries[0:50];
config['last-feed-time'] = pubentries[0]['published'];
process_template(config, 'atom-xml-template', 'atom.xml');

# archive/index.html
config['entries'] = pubentries;
last_year = '';
for v in pubentries:
    if (v['year'] != last_year):
        last_year = v['year'];
        v['new_year'] = True;
embedded_config = config.copy();
embedded_config['content'] = process_template(config, 'archive-index-content', None);
embedded_config['title'] = config['archive-index-title'];
process_template(embedded_config, 'page-template', 'index.html');
