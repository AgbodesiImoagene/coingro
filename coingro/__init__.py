""" Coingro bot """
import os


__version__ = 'develop'
__id__ = os.environ.get('CG_BOT_ID', 'coingro_bot')
__env__ = os.environ.get('CG_APP_ENV')
