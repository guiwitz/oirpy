import numpy as np
from pathlib import Path
import re
import struct


class Oirreader:
    """
    Class to read oir files.

    Parameters
    ----------
    filepath: str
        path to oir file

    Attributes
    ----------
    metadata: dict
        dictionary of metadata
    Buffer: binary file buffer
        file opened as binary

    """

    def __init__(
        self,
        filepath,
    ):

        self.filepath = Path(filepath)
        self.metadata = None
        self.buffer = None
        self.blocks = None

    def get_stack(self):
        """Extract complete stack of multi-channel image."""

        if self.buffer is None:
            with open(self.filepath, 'rb') as f:
                self.buffer = f.read()
        self.metadata = self.get_meta()
        blocks, full_blocks = self.find_blocks(self.metadata['NumberOfChannels'])
        images = [self.get_images(i) for i in range(self.metadata['NumberOfChannels'])]
        image = np.stack(images, axis=2)
        return image

    def get_images(self, channel):
        """Extract single plane out of data."""

        if self.metadata is None:
            self.metadata = self.get_meta()
        height = self.metadata['height']
        width = self.metadata['width']

        if self.blocks is None:
            self.blocks, _ = self.find_blocks(self.metadata['NumberOfChannels'])

        bytes_per_block = int(width * height/len(self.blocks))
        image_tot = np.zeros((height, width), dtype=np.uint16)
        lines_per_block = int(height/len(self.blocks))
        with open(self.filepath, 'rb') as f:
            for i in range(len(self.blocks)):
                f.seek(self.blocks[i][channel]-6)

                im_bytes = struct.unpack('<'+str(bytes_per_block)+'H', f.read(2*bytes_per_block))
                image = np.reshape(im_bytes, newshape=[lines_per_block, width])
                image_tot[i*lines_per_block:i*lines_per_block+lines_per_block, :] = image
        return image_tot

    def get_meta(self):
        """Extract metadata."""

        if self.buffer is None:
            with open(self.filepath, 'rb') as f:
                self.buffer = f.read()

        metadata = {}
        #Buffer = str(self.buffer)
        Buffer = self.buffer

        # parse metadata and find the lsmframe:frameProperties xml child
        # out of that get widht and height of image
        meta_type = b"lsmframe:frameProperties"
        start = Buffer.find(b'<'+meta_type)
        end = Buffer.find(b'</'+meta_type+b'>')
        xml = Buffer[start:end]

        cur_name = b'base:width'
        width = int(re.findall(b'.*'+cur_name+b'>(\d+)</.*', xml)[0])
        cur_name = b'base:height'
        height = int(re.findall(b'.*'+cur_name+b'>(\d+)</.*', xml)[0])
        metadata['height'] = height
        metadata['width'] = width

        metadata['channel_id'] = re.findall(b'\<commonframe\:channelImageDefinition channelId\=\"(.*?.*?)\"', xml)
        metadata['channel_id'] = [x.decode() for x in metadata['channel_id']]

        metadata['NumberOfChannels'] = len(metadata['channel_id'])
        # get some other chidlren
        # This is not used anymore but left as an example
        meta_type = b"lsmimage:imageProperties"
        start = self.buffer.find(b'<'+meta_type)
        end = self.buffer.find(b'</'+meta_type+b'>')
        xml = self.buffer[start:end]

        cur_name = 'lsmimage:dyeName>'
        channel_names = [re.findall(x+'.*?'+cur_name+'(.*?)</lsmimage:dyeName>?', str(xml))[-1] for x in metadata['channel_id']]
        metadata['channel_names'] = channel_names

        return metadata

    def find_blocks(self, NumberOfChannels):
        """Find location of pixel blocks."""

        blocks = {}
        full_blocks = {}
        for i in range(1000):

            # this pattern designs a block of pixels. We search for these blocks
            # within a region after the last block. If we don't find blocks we 
            # check the full file. This is designed to make regexp faster but taking
            # into account that in some cases large metadata might be interspersed.
            expr = bytes(str('_'+str(i)).encode("ascii"))+b'....'+b'\x04'
            if i == 0:
                find_match = list(re.finditer(expr, self.buffer))
                startpos = [x.end(0)+9 for x in find_match]
            else:
                find_match = list(re.finditer(expr, self.buffer[temp_block[-1]:temp_block[-1]+3*(temp_block[-1]-temp_block[0])]))
                startpos = [x.end(0)+9+temp_block[-1] for x in find_match]
                if len(startpos) == 0:
                    find_match = list(re.finditer(expr, self.buffer))
                    startpos = [x.end(0)+9 for x in find_match]

            #find_match = list(re.finditer(expr, self.buffer))
            #startpos = [x.end(0)+9 for x in find_match]
            temp_block = []
            full_blocks[i] = []
            for s in startpos:
                if 'REF' not in str(self.buffer[s-100:s]):
                    temp_block.append(s)
                    full_blocks[i].append(self.buffer[s-100:s])
            if len(temp_block) == 0:
                break
            blocks[i] = temp_block
        return blocks, full_blocks