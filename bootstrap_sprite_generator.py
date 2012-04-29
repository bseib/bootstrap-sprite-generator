#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import os
import math
import Image

#from bsg.iconfilter import GenericIconFilter, GenericIconFilter
from iconfilter import GenericIconFilter, GlyphIconFilter
from collections import OrderedDict

class SpriteGenerator(object):
    sprite_less_header = """
        #// This file automatically generated by bootstrap sprite generator
        #// https://github.com/plar/bootstrap-sprite-generator
        #
        #[class^="icon-"],
        #[class*=" icon-"] {
        #  display: inline-block;
        #  width: %(max_width)spx;
        #  height: %(max_height)spx;
        #  line-height: %(max_height)spx;
        #  vertical-align: text-top;
        #  background-image: url("@{iconSpriteProPath}");
        #  background-position: %(max_width)spx %(max_height)spx;
        #  background-repeat: no-repeat;
        #
        #  .ie7-restore-right-whitespace();
        #}
        #.icon-white {
        #  background-image: url("@{iconWhiteSpriteProPath}");
        #}
        #
        """
    
    sprite_less_item = """
        #.icon-%(name)-26s { background-position: %(ox)spx %(oy)spx; }
        #
        """
    
    def __init__(self, options, filter, filter_type):
        super(SpriteGenerator, self).__init__()
        self._options = options
        
        self._icon_filter = filter
        self._icon_type = filter_type
         
        self._icon_dir = options.icon_dir if options.icon_dir else filter.default_icon_dir 
        self._output_dir = options.output_dir if options.output_dir else filter.default_output_dir
        self._resize = options.resize

        
    def run(self):
        # load icons of specific _options.type from _options.icon_dir
        (icons, max_width, max_height) = self._load_icons()
    
        # generate sprite map and sprites-pro.less file
        self._generate_sprite_image(icons, max_width, max_height)
        self._generate_sprite_less(icons, max_width, max_height)
    
        # print icons
    
    def _load_icons(self):
        print "Load icons(%s) from %s directory..." % (self._icon_type, self._icon_dir)
        icons = OrderedDict()
        max_width = max_height = -1
        
        give_advice = True
        
        for file in os.listdir(self._icon_dir):
            icon_name = self._icon_filter.icon_name(self._icon_type, file)
            if not icon_name:
                continue

            # collect image info and dimension
            fimg = open("%s/%s" % (self._icon_dir, file), "rb")
            img = Image.open(fimg)
            img.load() # force load image
            if self._resize:
                img = img.copy()
                img.thumbnail((self._resize, self._resize), Image.ANTIALIAS)

            (w, h) = img.size
            if w > max_width:
                max_width = w
            if h > max_height:
                max_height = h

            # check for duplicated icon names            
            if icon_name in icons:
                if give_advice:
                    print "Advice: You can use '-m' parameter to redefine icon name for specific file"
                    give_advice = None
                print "Warning: icon '%s' already exists, file '%s', previous file '%s'" % (icon_name, file, icons[icon_name]['file_name'])
            
            icons[icon_name] = dict(icon_name=icon_name, file_name=file, image=img, width=w, height=h)
            
            fimg.close()
                    
        print "Total icons(%s): %d" % (self._icon_type, len(icons))
        print "Tile size: %dpx x %spx" % (max_width, max_height)
    
        return (icons, max_width, max_height)

    def _generate_sprite_image(self, icons, max_width, max_height):
        s = math.sqrt(len(icons))
        sprite_cols = int(math.ceil(s))
        sprite_rows = int(math.ceil(s))
        print "Sprite image size in tiles: %dx%d" % (sprite_cols, sprite_rows)
        
        sprite_width = sprite_cols * max_width
        sprite_height = sprite_rows * max_height
        print "Sprite image size in pixels: %dx%d" % (sprite_width, sprite_height)
    
        sprite_file_name = "%s/%s" % (self._output_dir, "sprites-pro.png")
        print "Creating sprite image %s..." % sprite_file_name
        sprite = Image.new(mode='RGBA', size=(sprite_width, sprite_height), color=(0, 0, 0, 0))  # transparent
        
        current_icon = 0
        for (unused, icon) in icons.items():
            ix = (current_icon % sprite_cols) * max_width
            iy = (current_icon / sprite_cols) * max_height
            
            icon['location'] = (ix, iy) # we need it for _less generation
            
            # adjust icon
            cx = (max_width - icon['width']) >> 1
            cy = (max_height - icon['height']) >> 1
            
            location = (ix + cx, iy + cy) 
            sprite.paste(icon['image'], location)
    
            current_icon += 1
            
        # save sprite
        try:
            os.makedirs(self._output_dir)
        except:
            pass
        
        sprite.save(sprite_file_name)
        print "Done"
        
        return
        
    def _generate_sprite_less(self, icons, max_width, max_height):
        
        css_file_name = "%s/%s" % (self._output_dir, "sprites-pro.less")
        print "Creating sprite css %s..." % css_file_name

        sprite_file = open(css_file_name, "w")
    
        # write css definition    
        sprite_file.write(self._get_as_text(self.sprite_less_header) % (dict(max_width=max_width, max_height=max_height)))
        
        # write each icon
        icon_line = self._get_as_text(self.sprite_less_item)
        for (icon_name, icon) in icons.items():
            (ox, oy) = icon['location']
            sprite_file.write(icon_line % (dict(name=icon_name, ox=-ox, oy=-oy)))

        sprite_file.close()    
        print "Done"
    
    def _get_as_text(self, block):
        lines = []
        for line in block.split("\n"):
            parts = line.split("#")
            if len(parts) == 2:
                lines.append(parts[1])
    
        return "\n".join(lines)

def main():
    parser = ArgumentParser(usage="%(prog)s [options]", description="Generate bootstrap sprite files for different icon libraries.", epilog="Supported icon libraries: GlyphIcon, FigueIcons and Generic Folders :)")
    parser.add_argument('-d', dest='icon_dir', help="icon files directory")
    parser.add_argument('-o', dest='output_dir', help="result files directory. if directory does not exist, it will be created automatically.")
    parser.add_argument('-r', dest='resize', help="resize original library icons to specific size(pixels)", default=None, type=int)
    parser.add_argument('-m', action='append', dest='adjust_map', help="adjust icon name for specific file. It option can be used multiply times. ie: -m glyphicons_079_signal.png:signal-strength")
    
    # prepare type argument
    supported_types = []
    filters = [GlyphIconFilter(), GenericIconFilter()]
    prefix2filter = dict()
    for filter in filters:
        prefix2filter[filter.prefix] = filter
        for type in filter.types:
            supported_types.append("%s:%s" % (filter.prefix, type))
    
    parser.add_argument('-t', dest='type', help="sprite generator type", choices=supported_types, required=True)
    args = parser.parse_args()

    # run selected generator    
    (filter, filter_type) = args.type.split(":")
    generator = SpriteGenerator(args, prefix2filter[filter], filter_type)
    generator.run()

if __name__ == "__main__":
    main()

