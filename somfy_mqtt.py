#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import os
import somfy_shutter
import cul

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control Somfy blinds via CUL RF USB stick')
    parser.add_argument('--cul', help='serial port with connected CUL device', required=True)
    parser.add_argument('--shutter', help='shutter to control', required=True)
    parser.add_argument('--command', help='command to send', required=True)
    args = parser.parse_args()

    if not os.path.exists(args.shutter + '.json'):
        raise ValueError('shutter %s not defined' % args.shutter)

    if not os.path.exists(args.cul):
        raise ValueError('cannot find CUL device %s' % args.cul)

    cul = cul.cul(args.cul)
    ss = somfy_shutter.somfy_shutter(args.shutter, cul)

    ss.send_command(args.command)
