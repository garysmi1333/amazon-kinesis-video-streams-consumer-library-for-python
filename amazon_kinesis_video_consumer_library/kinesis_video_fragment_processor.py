# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0.

'''
Amazon Kinesis Video Stream (KVS) Consumer Library for Python. 

This class provides post-processing fiunctions for a MKV fragement that has been parsed
by the Amazon Kinesis Video Streams Cosumer Library for Python. 

 '''
 
__version__ = "0.0.1"
__status__ = "Development"
__copyright__ = "Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved."
__author__ = "Dean Colcott <https://www.linkedin.com/in/deancolcott/>"

import io
import logging
import amazon_kinesis_video_consumer_library.ebmlite.util as emblite_utils

# Init the logger.
log = logging.getLogger(__name__)

class KvsFragementProcessor():

    ####################################################
    # Fragment processing functions

    def get_fragment_tags(self, fragment_dom):
        '''
        Parses a MKV Fragment Doc (of type ebmlite.core.MatroskaDocument) that is returned to the provided callback 
        from get_streaming_fragments() in this class and returns a dict of the SimpleTag elements found. 

        ### Parameters:

            **fragment_dom**: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite. 

        ### Returns:

            simple_tags: dict

            Dictionary of all SimpleTag elements with format -  TagName<String> : TagValue <String | Binary>. 

        '''

        # Get the Segment Element of the Fragment DOM - error if not found
        segment_element = None
        for element in fragment_dom:
            if (element.id == 0x18538067):          # MKV Segment Element ID
                segment_element = element
                break
        
        if (not segment_element):
            raise KeyError('Segment Element required but not found in fragment_doc' )

        # Save all of the SimpleTag elements in the Segment element
        simple_tag_elements = []
        for element in segment_element:
            if (element.id == 0x1254C367):                      # Tags element type ID
                    for tags in element:
                        if (tags.id == 0x7373):                 # Tag element type ID
                            for tag_type in tags:
                                if (tag_type.id == 0x67C8 ):    # SimpleTag element type ID
                                    simple_tag_elements.append(tag_type)

        # For all SimpleTags types (ID: 0x67C8), save for TagName (ID: 0x7373) and values of TagString (ID:0x4487) or TagBinary (ID: 0x4485 )
        simple_tags_dict = {}
        for simple_tag in simple_tag_elements:

            tag_name = None
            tag_value = None
            for element in simple_tag:
                if (element.id == 0x45A3):                              # Tag Name element type ID
                    tag_name = element.value
                elif (element.id == 0x4487 or element.id == 0x4485):    # TagString and TagBinary element type IDs respectively
                    tag_value = element.value
            
            # As long as tag name was found add the Tag to the return dict. 
            if (tag_name):
                simple_tags_dict[tag_name] = tag_value

        return simple_tags_dict
    
    def get_fragement_dom_pretty_string(self, fragment_dom):
        '''
        Returns the Pretty Print parsing of the EBMLite fragment DOM as a string

        ### Parameters:

            **fragment_dom**: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite. 

        ### Return:
            **pretty_print_str**: str
                Pretty print string of the Fragment DOM object
        '''
        
        pretty_print_str = io.StringIO()

        emblite_utils.pprint(fragment_dom, out=pretty_print_str)
        return pretty_print_str.getvalue()

    def get_aws_connect_track_info(self, fragment_dom):
            '''
            Returns Audio Track Information

            Whether AUDIO_FROM_CUSTOMER and/or AUDIO_TO_CUSTOMER is populated depends upon
            whenever either was set when setting up Call Streaming in the AWS Connect Call Flow
            {
                "AUDIO_FROM_CUSTOMER": {
                    "track_number": None,
                    "track_identifying_byte": None,
                    "track_uid": None,
                    "track_type": None,
                    "track_codec_id": None
                },
                "AUDIO_TO_CUSTOMER": {
                    "track_number": None,
                    "track_identifying_byte": None,
                    "track_uid": None,
                    "track_type": None,
                    "track_codec_id": None
                }
            }

            ### Parameters:

                **fragment_dom**: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                    The DOM like structure describing the fragment parsed by EBMLite. 

            ### Return:
                **track_information**: object
                    Contains information about the tracks received
            '''

            segment_element = None
            for element in fragment_dom:
                if (element.id == 0x18538067):          # MKV Segment Element ID
                    segment_element = element
                    break
            
            if (not segment_element):
                raise KeyError('Segment Element required but not found in fragment_doc' )

            track_information = {
            }

            for element in segment_element:
                if (element.id == 0x1654AE6B):                  # Tracks Master Element ID
                    for trackentry in element:
                        track_number = None
                        track_uid = None
                        track_type = None
                        track_codec_id = None
                        track_name = None
                        for track_info in trackentry:
                            if (track_info.id == 0xD7):         # Track Number Element ID
                                track_number = track_info.value
                            elif (track_info.id == 0x73C5):     # Track UID Element ID
                                track_uid = track_info.value
                            elif (track_info.id == 0x83):       #Track Type Element ID
                                track_type = track_info.value   # Should always be 2 for Audio
                            elif (track_info.id == 0x86):       # Track Codec Element ID
                                track_codec_id = track_info.value
                            elif (track_info.id == 0x536E):     # Track Name Element ID
                                track_name = track_info.value   # Should contain either AUDIO_FROM_CUSTOMER or AUDIO_TO_CUSTOMER
                            if (track_name and track_name not in track_information):
                                track_information[track_name] = {}
                                track_information[track_name]["track_number"] = track_number
                                track_information[track_name]["track_uid"] = track_uid
                                track_information[track_name]["track_type"] = track_type
                                track_information[track_name]["track_codec_id"] = track_codec_id

            return track_information
        
    def get_aws_connect_customer_audio(self, fragment_dom):
        '''
        Returns the actual audio bytes received for each track

        One bytearray for each track present:

        {
            "track_1": bytearray(),
            "track_2": bytearray()
        }
    
        The bytes can be written directly to file, for example using python builtin wave library or futher
        audio processing can be done

        ### Parameters:

            **fragment_dom**: ebmlite.core.Document <ebmlite.core.MatroskaDocument>
                The DOM like structure describing the fragment parsed by EBMLite. 

        ### Return:
            **track_audio_data**: dict
                The audio data received
        '''

        segment_element = None
        for element in fragment_dom:
            if (element.id == 0x18538067):          # MKV Segment Element ID
                segment_element = element
                break
        
        if (not segment_element):
            raise KeyError('Segment Element required but not found in fragment_doc' )
        
        simple_block_elements = []
        for element in segment_element:
            if element.id == 0x1F43B675:
                for tags in element:
                    if tags.id == 0xA3:				# Simple Blocks Element ID
                        simple_block_elements.append(tags)

        track_audio_data = {
            "track_1": bytearray(),
            "track_2": bytearray()
        }

        for simple_block in simple_block_elements:
            track_number_byte = simple_block.value[0]   # first byte contains track number in VINT encoding
            new_block = simple_block.value[4:]          # first four bytes are headers so ignore

            if track_number_byte == 0x81:               # 0x81 VINT encoding of decimal 1
                track_audio_data['track_1'].extend(new_block)
            elif track_number_byte == 0x82:             # 0x82 VINT encoding of decimal 2
                track_audio_data['track_2'].extend(new_block)

        return track_audio_data
