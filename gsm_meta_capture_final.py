#!/usr/bin/env python2
##################################################
# A modified GNU Radio Python Flow Graph
# Title: GSM Signal Capture v3.grc
# Author: Varun Nambiar
# Generated: Fri Jul 10 10:18:29 2015
##################################################

import sys
import struct
import time
import pmt
import math

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio import gr, blocks
from gnuradio import uhd
from gnuradio.blocks import parse_file_metadata
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import time

class gsm_meta_capture(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Gsm Meta Capture")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 1e6

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(906.2e6, 0)
        self.uhd_usrp_source_0.set_gain(10, 0)
        self.single_pole_iir_filter_xx_0 = filter.single_pole_iir_filter_ff(.0001, 1)
        self.blocks_keep_one_in_n_0 = blocks.keep_one_in_n(gr.sizeof_float*1, 13300)
        self.blocks_file_meta_sink_0 = blocks.file_meta_sink(gr.sizeof_float*1, "meta_signal.bin", samp_rate, 1, blocks.GR_FILE_FLOAT, False, 10, "", False)
        self.blocks_file_meta_sink_0.set_unbuffered(False)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.band_pass_filter_0 = filter.fir_filter_ccf(1, firdes.band_pass(
        	1, samp_rate, 200e3, 400e3, 200, firdes.WIN_HAMMING, 6.76))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.band_pass_filter_0, 0), (self.blocks_complex_to_mag_squared_0, 0))    
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.single_pole_iir_filter_xx_0, 0))    
        self.connect((self.blocks_keep_one_in_n_0, 0), (self.blocks_file_meta_sink_0, 0))    
        self.connect((self.single_pole_iir_filter_xx_0, 0), (self.blocks_keep_one_in_n_0, 0))    
        self.connect((self.uhd_usrp_source_0, 0), (self.band_pass_filter_0, 0))    


    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.band_pass_filter_0.set_taps(firdes.band_pass(1, self.samp_rate, 200e3, 400e3, 200, firdes.WIN_HAMMING, 6.76))


if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = gsm_meta_capture()
    tb.start()
    
    # store time when gnuradio program starts capturing GSM signals
    floatTime = time.time()
    try:
        raw_input('Press Enter to quit: ')
    except EOFError:
        pass

    tb.stop()
    tb.wait()

    fileToWrite = open("signal.txt", 'w')
    fileToRead = open("meta_signal.bin", "rb")

    posInFile = 0
    while(True):
        header_str = fileToRead.read(parse_file_metadata.HEADER_LENGTH)
        if(len(header_str) == 0):
            break
        try:
            header = pmt.deserialize_str(header_str)
        except RuntimeError:
            sys.stderr.write("Could not deserialize header: invalid or corrupt data file.\n")
            sys.exit(1)

        info = parse_file_metadata.parse_header(header, False)

        if(info["extra_len"] > 0):
            extra_str = fileToRead.read(info["extra_len"])
            if(len(extra_str) == 0):
                break

            try:
                extra = pmt.deserialize_str(extra_str)
            except RuntimeError:
                sys.stderr.write("Could not deserialize extras: invalid or corrupt data file.\n")
                sys.exit(1)
        
        posInFile += parse_file_metadata.HEADER_LENGTH + info["extra_len"]
        fileToWrite.write(time.asctime(time.localtime(floatTime+info["rx_time"])) + '\n')
        for x in range(0, info["nitems"]):
            fileToRead.seek(posInFile + x * 4, 0)
            signal = struct.unpack("f", fileToRead.read(4))[0]
            fileToWrite.write(str(10*math.log10(float(signal))) + '\n')
            
        posInFile += info['nbytes']
        fileToRead.seek(posInFile, 0)
