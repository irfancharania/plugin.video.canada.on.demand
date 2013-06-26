from theplatform import *
from BeautifulSoup import BeautifulStoneSoup
try:
    from pyamf import remoting
    has_pyamf = True
except ImportError:
    has_pyamf = False

class AstralBaseChannel(ThePlatformBaseChannel):
    is_abstract = True
    base_url = 'http://www.family.ca'
    PID = None
    root_depth = 1

    def get_categories_json(self,arg=None):
        return ThePlatformBaseChannel.get_categories_json(self) # + '&query=ParentIDs|%s'%arg

    def get_releases_json(self,arg='0'):
        return ThePlatformBaseChannel.get_releases_json(self) + '&query=CategoryIDs|%s'% (self.args['entry_id'],)


    def get_cached_categories(self, parent_id):

        categories = None

        fpath = os.path.join(self.plugin.get_cache_dir(), 'canada.on.demand.%s.categories.cache' % (self.get_cache_key(),))
        try:
            if os.path.exists(fpath):
                data = simplejson.load(open(fpath))
                if data['cached_at'] + self.category_cache_timeout >= time.time():
                    logging.debug("using cached Categories")
                    categories = data['categories']
        except:
            logging.debug("no cached Categories path")

        if not categories:
            logging.debug('http-retrieving categories')
            url = self.get_categories_json(parent_id)
            logging.debug('get_cached_categories(p_id=%s) url=%s'%(parent_id, url))

            categories = []
            categories = self.parse_callback(self.plugin.fetch(url, self.cache_timeout).read())
            if self.category_cache_timeout > 0:
                fpath = os.path.join(self.plugin.get_cache_dir(), 'canada.on.demand.%s.categories.cache' % (self.short_name,))
                fh = open(fpath, 'w')
                simplejson.dump({'cached_at': time.time(), 'categories': categories}, fh)
                fh.close()

        return categories

    def get_categories(self, parent_id=None):
        categories = self.get_cached_categories(parent_id)
        #logging.debug(categories)

        cats = []
        for c in categories:
            #logging.debug(c)

            data = {}
            data.update(self.args)

            data.update({
                'entry_id': c["id"],
                #'Thumb': self.base_url + c['imagePath'] + c['image'],
                'Title': decode_htmlentities(c['title']),
                #'Plot': c['description'],
                'action': 'browse',
                'force_cache_update': False,
            })

            cats.append(data)

        logging.debug("get_categories cats=%s"%cats)
        return cats

    def action_browse(self):
        releases = self.get_releases(self.args)
        logging.debug("Got %s Releases: %s" % (len(releases), "\n".join(repr(r) for r in releases)))
        for rel in releases:
            self.plugin.add_list_item(rel, is_folder=False)
        self.plugin.end_list('episodes', [xbmcplugin.SORT_METHOD_DATE])


    def get_releases(self, parameter):
        logging.debug('get_releases (parameter=%s)'%parameter)

        url = self.get_releases_json(parameter)
        logging.debug('get_releases url=%s'%url)

        data = self.parse_callback(self.plugin.fetch(url, max_age=self.cache_timeout).read())['video']
        #max_bitrate = int(self.plugin.get_setting('max_bitrate'))

        rels = []
        for item in data:
            action = 'play'

            rels.append({
                'Thumb': self.base_url + item['imagePath'] + item['image'],
                'Title': item['title'],
                'Plot': item['description'],
                #'Date': item['startDate'],
                'entry_id': item['id'],
                'remote_url': item['filename'],
                'channel': self.args['channel'],
                'action': action,
                'medialen': item['length']
            })

        return rels

    def action_play(self):
        parse = URLParser(swf_url=self.swf_url, playpath_qs=False)
        self.plugin.set_stream_url(parse(self.args['clip_url']))


    def action_root(self):
        logging.debug('ThePlatformBaseChannel::action_root')
        parent_id = self.args['entry_id'] # this should be None from @classmethod
        if parent_id == 'None':
            parent_id = None
        categories = self.get_categories(parent_id)# and root=true
        for cat in categories:
            self.plugin.add_list_item(cat)
        self.plugin.end_list()


#class Family(AstralBaseChannel):
#    short_name = 'family'
#    long_name = 'Family.ca'
#    base_url = "http://www.family.ca"

# staticCats: ["featured", "all", "rated", "most", "recent"],

#
#    def get_categories_json(self,arg=None):
#        url = 'http://www.family.ca/video/scripts/getCats.php'
#        logging.debug('get_categories_json: %s'%url)
#        return url
#
#    def get_releases_json(self,arg='0'):
#        url = 'http://www.family.ca/video/scripts/getVids.php?id=%s&page=1' % self.args['entry_id']
#        logging.debug('get_releases_json: %s'%url)
#        return url
#

class Disney(AstralBaseChannel):
    short_name = 'disneyxd'
    long_name = 'Disney XD'
    base_url = "http://www.disneyxd.ca"

    def get_categories_json(self,arg=None):
        url = self.base_url + '/video/scripts/getCats.php'
        logging.debug('get_categories_json: %s'%url)
        return url

    def get_releases_json(self,arg='0'):
        url = self.base_url + '/video/scripts/getVids.php?id=%s&page=1' % self.args['entry_id']
        logging.debug('get_releases_json: %s'%url)
        return url

    def action_play(self):
        urltemplate = 'http://video.disneyxd.ca/%s'
        url = urltemplate % self.args['remote_url']
        return self.plugin.set_stream_url(url)


#http://video.disneyxd.ca/DXD_TronMusicVideo.mp4