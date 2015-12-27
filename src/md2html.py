#!/usr/bin/env python
# -*- coding: utf-8 -*-

import markdown, pystache, yaml;
import datetime, json, re, os, shutil, sys;

config = {};
inputDir = os.path.dirname(sys.argv[-1]);

# load config files except for the last argument
for i in range(1, len(sys.argv)-1):
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

# load last argument
with (open(sys.argv[-1], 'r')) as f:
    fileText = f.read();
yamlMatch = re.compile(r'^---\n(.*)\n---\n(.*)', re.DOTALL).match(fileText);
yamlText = yamlMatch.group(1);
mdText = yamlMatch.group(2);
ymap = yaml.load(yamlText);
for k in ymap:
    config[k] = ymap[k];

# load data file
if ('data-file' in config) and (config['data-file'].endswith('.json')):
    with (open(inputDir + '/' + config['data-file'], 'r')) as f:
        jmap = json.load(f);
        for k in jmap:
            config[k] = jmap[k];

# set draft flag if published ts is in the future
now = str(datetime.datetime.now()).replace(' ', 'T')[0:-3];
if ('published' in config):
    published = str(config['published']);
    if (published > now):
        config['draft'] = True;

# create a subset of properties for the archive DB
datamap = {};
for key in ['url', 'lang', 'title', 'draft', 'description', 'summary', 'published', 'updated', 'author', 'tag', 'category']:
    if (key in config):
        datamap[key] = str(config[key]);

# update properties in the archive DB
noarchive = ('no-archive' in config) and (config['no-archive'] == True);
if (not noarchive) and ('archive-json' in config) and (os.path.exists(config['archive-json'])):
    with (open(config['archive-json'], 'r')) as f:
        jmap = json.load(f);
        same = False;
        if config['url'] in jmap:
            dbmap = jmap[config['url']];
            same = len(set(dbmap.items()) ^ set(datamap.items())) == 0;
        if not same:
            jmap[config['url']] = datamap;
            with open(config['archive-json'], 'w') as outfile:
                json.dump(jmap, outfile, sort_keys=True, indent=2);

# no work with draft posts
if ('draft' in config) and (config['draft'] == True):
    exit(0);

# transform the list of lang:url maps into a better suited map
if 'translation' in config:
    newhreflang = [];
    for m in config['translation']:
        for k in m:
            v = m[k];
            newhreflang.append({'lang': k, 'href': v});
    config['translation'] = newhreflang;

# run markdown
md = markdown.Markdown(extensions = [
    'markdown.extensions.extra',
    'markdown.extensions.meta',
    'markdown.extensions.sane_lists',
    'markdown.extensions.toc(baselevel=2,marker="")'])

# create context for mustache
config['content'] = md.convert(mdText);
config['md-meta'] = md.Meta;
if ('toc' in config) and (config['toc'] == True):
    config['md-toc'] = md.toc;

if (not 'output-file' in config):
    if config['url'].endswith('.html'):
        config['output-file'] = config['url'];
    else:
        if config['url'].endswith('/'):
            config['output-file'] = config['url'] + 'index.html';

with (open(config['page-template'], 'r')) as f:
    mustacheText = f.read();
newHtmlText = pystache.render(mustacheText, config);

htmlFileName = config['output-dir'] + config['output-file'];
outputDir = os.path.dirname(htmlFileName);
if not os.path.exists(outputDir):
    print('Creating: ' + outputDir);
    os.makedirs(outputDir)

# Writing output HTML
oldHtmlText = '';
if os.path.exists(htmlFileName):
    with (open(htmlFileName, 'rb')) as f:
        oldHtmlText = f.read().decode('utf-8');
if newHtmlText != oldHtmlText:
    print('Writing: ' + htmlFileName);
    with open(htmlFileName, 'wb') as f:
        f.write(newHtmlText.encode('utf-8'));

# copy referenced assets
assets = [];
if 'asset' in config:
    for a in config['asset']:
        assets.append(a);
for m in re.compile(r'src=\"(.*?)\"').findall(config['content']):
    assets.append(m);
if 'cover-image' in config:
    assets.append(config['cover-image']);

for src in assets:
    fullSrc = inputDir + '/' + src;
    if '/' in src:
        continue;
    if not os.path.isfile(fullSrc):
        continue;
    dest = outputDir + '/' + src;
    doCopy = False;
    if os.path.isfile(dest):
        doCopy = os.path.getmtime(fullSrc) > os.path.getmtime(dest);
    else:
        doCopy = True;
    if doCopy:
        print('Copy: ' + fullSrc + ' -> ' + dest);
        shutil.copy2(fullSrc, dest);
