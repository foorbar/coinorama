#!/usr/bin/python
#
# Coinorama/coinref: watch and store raw Bitcurex EUR market info
#
# This file is part of Coinorama <http://coinorama.net>
#
# Copyright (C) 2013-2016 Nicolas BENOIT
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import time
import traceback
import httplib
import coinwatcher


# Watcher class
class BitcurexEURWatcher (coinwatcher.CoinWatcher) :
    def __init__ ( self, shortname, with_coinrefd, logger ):
        coinwatcher.CoinWatcher.__init__ ( self, shortname, with_coinrefd, logger )
        self.mostRecentTransactionID = 0
        self.mostRecentPrice = 0
        self.EUR_USD_rate = 1.0885
        self.EUR_USD_stamp = 0

    def buildData ( self, book, trades, lag ):
        ed = coinwatcher.ExchangeData ( )

        mostRecentID = self.mostRecentTransactionID
        mostRecentPrice = self.mostRecentPrice
        try:
            for t in trades:
                tid = int ( t['tid'] )
                if ( 'ammount' in t ):
                    tvol = float ( t['ammount'] )
                else:
                    tvol = float ( t['amount'] )
                tdate = float ( t['date'] )
                if ( ( tid > self.mostRecentTransactionID ) and ( tdate > self.epoch ) ):
                    ed.volume += tvol
                    ed.nb_trades += 1
                if ( tid > mostRecentID ):
                    mostRecentID = tid
                    mostRecentPrice = float ( t['price'] )
        except Exception:
            self.logger.write ( 'error buildData trades\n' + str(traceback.format_exc()) )
            return None

        try:
            bstr = 'bids'
            astr = 'asks'
            if ( float(book['bids'][0][0]) > float(book['asks'][0][0]) ):
                bstr = 'asks'
                astr = 'bids'
            maxbprice = max ( [ float(b[0]) for b in book[bstr] ] )
            for b in book[bstr]:
                bprice = float ( b[0] )
                bvol = float ( b[1] )
                if ( (maxbprice-bprice) < 700 ):
                    ed.bids.append ( [ bprice, bvol ] )
                ed.total_bid += bprice * bvol
            ed.bids.sort ( reverse=True )

            minaprice = min ( [ float(a[0]) for a in book[astr] ] )
            for a in book[astr]:
                aprice = float ( a[0] )
                avol = float ( a[1] )
                if ( (aprice-minaprice) < 700 ):
                    ed.asks.append ( [ aprice, avol ] )
                ed.total_ask += avol
            ed.asks.sort ( )
        except Exception:
            self.logger.write ( 'error buildData book\n' + str(traceback.format_exc()) )
            return None

        try:
            if ( mostRecentID != 0 ):
                self.mostRecentPrice = mostRecentPrice
            if ( self.mostRecentPrice == 0 ):
                self.mostRecentPrice = ed.bids[0][0]
            if ( mostRecentID != 0 ):
                self.mostRecentTransactionID = mostRecentID
            ed.rate = self.mostRecentPrice
            ed.lag = lag
            ed.ask_value = ed.asks[0][0]
            ed.bid_value = ed.bids[0][0]
            ed.USD_conv_rate = self.EUR_USD_rate
        except Exception:
            self.logger.write ( 'error buildData ticker\n' + str(traceback.format_exc()) )
            return None

        return ed

    def fetchData ( self ):
        if ( (time.time()-self.EUR_USD_stamp) > 3600.0 ): # get USD/EUR rate every hour
            try:
                connection = httplib.HTTPConnection ( 'download.finance.yahoo.com', timeout=5 )
                connection.request ( 'GET', '/d/quotes.csv?s=EURUSD=X&f=sl1&e=.csv' )
                r = connection.getresponse ( )
                if ( r.status == 200 ):
                    rate_txt = r.read ( )
                    rate = float ( rate_txt.split(',')[1] )
                    if ( rate > 0 ):
                        self.EUR_USD_rate = rate
                        self.EUR_USD_stamp = time.time ( )
                        #self.logger.write ( 'rate: %f ' % self.EUR_USD_rate )
                else:
                    self.logger.write ( 'error EUR_USD http %d' % r.status )
                connection.close ( )
            except Exception:
                self.logger.write ( 'error EUR_USD\n' + str(traceback.format_exc()) )
                pass

        ed = coinwatcher.CoinWatcher.fetchData ( self, httplib.HTTPSConnection, 'bitcurex.com', '/api/eur/orderbook.json', '/api/eur/trades.json' )
        return ed


#
#
# main program
#

if __name__ == "__main__":
    coinwatcher.main ( 'Bitcurex-EUR', 'bitcurexEUR', BitcurexEURWatcher )
