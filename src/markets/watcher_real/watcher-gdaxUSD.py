#!/usr/bin/python
#
# Coinorama/coinref: watch and store raw Coinbase USD market info
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
import datetime
import traceback
import httplib
import coinwatcher


# Watcher class
class GDAXUSDWatcher (coinwatcher.CoinWatcher) :
    def __init__ ( self, shortname, with_coinrefd, logger ):
        coinwatcher.CoinWatcher.__init__ ( self, shortname, with_coinrefd, logger )
        self.mostRecentTransaction = ( time.time() - 1 )
        self.mostRecentTransactionID = 0
        self.mostRecentPrice = 0
        #self.book = None
        #self.book_fetch_full = True
        #self.book_stamp = 0

    def buildData ( self, book, trades, lag ):
        ed = coinwatcher.ExchangeData ( )

        mostRecentID = self.mostRecentTransactionID
        mostRecentDate = 0
        mostRecentPrice = self.mostRecentPrice
        try:
            for t in trades:
                tid = int ( t['trade_id'] )
                tvol = float ( t['size'] )
		ttime=t['time']
                d = datetime.datetime.strptime ( ttime[:-5], '%Y-%m-%dT%H:%M:%S' )
                tdate = float ( d.strftime('%s') ) - time.timezone
                if ( ( tid > self.mostRecentTransactionID ) and ( tdate > self.epoch ) ):
                    ed.volume += tvol
                    ed.nb_trades += 1
                if ( tid > mostRecentID ):
                    mostRecentID = tid
                    mostRecentDate = tdate
                    mostRecentPrice = float ( t['price'] )
        except Exception as e:
            self.logger.write ( 'error buildData %s' % e )
            return None

        #if ( self.book_fetch_full ):
        #    self.book = book
        #    self.book_fetch_full = False
        #else:
        #    book = self.book

        try:
            for b in book['bids']:
                bprice = float ( b[0] )
                bvol = float ( b[1] )
                ed.bids.append ( [ bprice, bvol ] )
                ed.total_bid += bprice * bvol
            ed.bids.sort ( reverse=True )

            for a in book['asks']:
                aprice = float ( a[0] )
                avol = float ( a[1] )
                ed.asks.append ( [ aprice, avol ] )
                ed.total_ask += avol
            ed.asks.sort ( )
        except Exception as e:
            self.logger.write ( 'error buildData %s' % e )
            return None

        try:
            if ( mostRecentID != 0 ):
                self.mostRecentPrice = mostRecentPrice
            if ( self.mostRecentPrice == 0 ):
                self.mostRecentPrice = ed.bids[0][0]
            if ( mostRecentID != 0 ):
                self.mostRecentTransactionID = mostRecentID
                self.mostRecentTransaction = mostRecentDate
            ed.rate = self.mostRecentPrice
            ed.lag = lag
            ed.ask_value = ed.asks[0][0]
            ed.bid_value = ed.bids[0][0]
        except Exception as e:
            self.logger.write ( 'error buildData %s' % e )
            return None

        return ed

    def fetchData ( self ):
        trades = '/products/BTC-USD/trades'
        #book = '/products/BTC-USD/book?level=2'
        #if ( (time.time() - self.book_stamp) > 30 ):
        #    self.book_fetch_full = True
        #    book = '/products/BTC-USD/book?level=3'
        #    self.book_stamp = time.time ( )
        book = '/products/BTC-USD/book?level=3'
        ed = coinwatcher.CoinWatcher.fetchData ( self, httplib.HTTPSConnection, 'api.gdax.com', book, trades )
        return ed



#
#
# main program
#

if __name__ == "__main__":
    coinwatcher.main ( 'GDAX-USD', 'gdaxUSD', GDAXUSDWatcher )
