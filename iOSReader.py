#!/usr/bin/env python3
# encoding: utf-8
import sqlite3
import operator
import os
import re
import sys
import datetime

class reader():

    """A class for the easy analysis of iOS text message databases."""

    def __init__(self):
        """

        Initializes the reader instance variables.

        """
        # sqlite3 connection to the message database.
        self._connSMS = None
        # sqlite3 connection to the contacts database.
        self._connAdd = None
        # Dictionary for caching of the numbers that handles refer to.
        self._handleDict = {}
        # Dictionary for caching the total number of words for each number.
        self._wordDict = {}
        # Dictionary for caching the total number of messages for each number.
        self._countDict = {}
        # Boolean which defines whether the dictionaries have been built.
        self._built = False

    def lastDate(self):
        
        """ Returns the date of the most recent message in the database. """
        
        c = self._connSMS.cursor()
        c.execute("SELECT `date` FROM `message`  ORDER BY `date` DESC LIMIT 0, 1;")
        mostrecent = c.fetchone()[0]
        return self._intToDate(mostrecent)

    def getNameFromNumber(self, number):
        
        """ Returns the name in the addressbook that corresponds to the number argument. """
        
        # Crops the number to the last four digits
        # TODO: Fix this in the event two people share the same last four
        # digits.
        lastfour = str(number)[-4:]
        a = self._connAdd.cursor()
        # Fetch the id that corresponds to the last four digits.
        a.execute("SELECT multivalue_id FROM `ABPhoneLastFour` WHERE 1=1 AND `value` LIKE '" + lastfour + "' ORDER BY `value` DESC LIMIT 0, 50000;")
        lastFourRow = a.fetchone()
        # If there isn't an id, the name is the number.
        if lastFourRow is None:
            return str(number)
        multiId = lastFourRow[0]
        # SQL to go from id to name.
        a.execute("SELECT record_id FROM `ABMultiValue` WHERE 1=1 AND `UID` LIKE '" + str(multiId) + "' ORDER BY `_rowid_` ASC LIMIT 0, 50000;")
        personId = a.fetchone()[0]
        a.execute("SELECT First, Last FROM `ABPerson` WHERE 1=1 AND `ROWID` LIKE '" + str(personId) + "' ORDER BY `_rowid_` ASC LIMIT 0, 50000;")
        personRow = a.fetchone()
        # Use only the first two words in the name.
        # TODO: Correct this, its no longer needed.
        if personRow[1] is not None:
            name = personRow[0] + " " + personRow[1].split()[0]
        else:
            name = personRow[0]
        return name

    def getNumberFromHandle(self, handle):
        
        """ Returns the number that corresponds to the given handle argument. """
        
        # If the handle is in the cache, return it from the cache.
        if handle in self._handleDict.keys():
            return self._handleDict[handle]
        # Otherwise match it with SQL and add it to the cache.
        else:
            d = self._connSMS.cursor()
            d.execute("SELECT `id` FROM `handle` WHERE 1=1 AND `ROWID` LIKE '" + str(handle) + "' ORDER BY `_rowid_` ASC LIMIT 0, 1;", )
            result = d.fetchone()
            if result is not None:
                self._handleDict[handle] = result[0]
                return result[0]
            else:
                self._handleDict[handle] = None
                return None

    def numbersFromName(self, name):
        
        """ Returns the list of numbers that match a given name. """
        
        numbers = []
        # Check each number to see if it matches the name.
        for number in self.getListOfNumbers():
            if self.getNameFromNumber(number) == name:
                numbers.append(number)
        return numbers


    def addAddressBook(self, path):
        
        """ Creates a database connection to the addressbook with a given path. """
        
        assert os.path.exists(path) and self._connAdd is None
        self._connAdd = sqlite3.connect(path)

    def addSMSDatabase(self, path):
        
        """ Creates a database connection to the messages with a given path. """
        
        assert os.path.exists(path) and self._connSMS is None
        self._connSMS = sqlite3.connect(path)

    def _build(self):
        
        """ Builds the dictionaries. """
        
        self._buildHandleDict()
        self._buildOthers()
        self._built = True
        
    def _buildHandleDict(self):
        
        """ Builds the handle dictionary. """
        
        c = self._connSMS.cursor()
        c.execute("SELECT DISTINCT `handle_id` FROM `message`  ORDER BY `handle_id`;")
        handleList = c.fetchall()
        for handletuple in handleList:
            handle = handletuple[0]
            if handle == 0:
                continue
            self.getNumberFromHandle(handle)

    def _buildOthers(self):
        
        """ Builds the other dictionaries. """
        
        c = self._connSMS.cursor()
        for key in self._handleDict.keys():
            number = self._handleDict[key]
            if number not in self._countDict.keys():
                self._countDict[number] = 0
            if number not in self._wordDict.keys():
                self._wordDict[number] = 0
            c.execute("SELECT `text` FROM 'message' WHERE handle_id=" + str(key))
            messageList = c.fetchall()
            for messagetuple in messageList:
                message = messagetuple[0]
                self._countDict[number] += 1
                if message is not None:
                    self._wordDict[number] += len(re.findall("[a-zA-Z_]+", message))


    def totalMessages(self):
        
        """ Returns the total number of messages in the database. """
        
        c = self._connSMS.cursor()
        c.execute("SELECT COUNT(text) FROM `message`")
        return c.fetchone()[0]
    
    def getListOfNumbers(self):
        
        """ Returns a list of all of the numbers in the messages database. """
        
        if not self._built:
            self._build()
        return set(self._handleDict.values())

    def messagesOnDate(self, date, number = None):
        
        """ Returns a list of messages on a given date, optionally from a given number. """
        
        messages = []
        beg = self._dateToInt(datetime.datetime.combine(date, datetime.time(0)))
        end = self._dateToInt(datetime.datetime.combine(date, datetime.time(0)) + datetime.timedelta(days = 1))
        c = self._connSMS.cursor()
        if not number:
            c.execute("SELECT `handle_id`, `date`, `text` FROM `message` WHERE 1=1 AND `date` > ? AND `date` < ?;", (beg, end))
            rows = c.fetchall()
            for mes in rows:
                if mes[2] is not None:
                    message = Message(mes[2])
                    message.number = self.getNumberFromHandle(mes[0])
                    message.timestamp = self._intToDate(mes[1])
                    messages.append(message)
        else:
            for handle in self._getHandlesFromNumber(number):
                c.execute("SELECT `handle_id`, `date`, `text` FROM `message` WHERE 1=1 AND `date` > ? AND `date` < ? AND `handle_id` = ?;", (beg, end, handle))
                rows = c.fetchall()
                for mes in rows:
                    if mes[2] is not None:
                        message = Message(mes[2])
                        message.number = self.getNumberFromHandle(mes[0])
                        message.timestamp = self._intToDate(mes[1])
                        messages.append(message)

        return messages

    def countOnDate(self, date, number = None):
        
        """ Returns the count of messages on a given date, optionally from a given number. """
        
        if not self._built:
            self._build()
        beg = self._dateToInt(datetime.datetime.combine(date, datetime.time(0)))
        end = self._dateToInt(datetime.datetime.combine(date, datetime.time(0)) + datetime.timedelta(days = 1))
        c = self._connSMS.cursor()
        count = 0
        if not number:
            c.execute("SELECT COUNT(*) FROM `message` WHERE `date` >= ? AND `date` < ? AND `text` IS NOT NULL;", (beg, end))
            count = c.fetchone()[0]
        else:
            for handle in self._getHandlesFromNumber(number):
                c.execute("SELECT COUNT(*) FROM `message` WHERE 1=1 AND `date` > ? AND `date` < ? AND `handle_id` = ? AND `text` IS NOT NULL;", (beg, end, handle))
                count += c.fetchone()[0]
        return count 

    def totalOnDate(self, date, number = None):
        
        """ Returns the overall total number of messages on a given date, optionally from a given number. """
        
        if not self._built:
            self._build()
        end = self._dateToInt(datetime.datetime.combine(date, datetime.time(0)) + datetime.timedelta(days = 1))
        c = self._connSMS.cursor()
        count = 0
        if not number:
            c.execute("SELECT COUNT(*) FROM `message` WHERE `date` < " + str(end) + " AND `text` IS NOT NULL;")
            count = c.fetchone()[0]
        else:
            for handle in self._getHandlesFromNumber(number):
                c.execute("SELECT COUNT(*) FROM `message` WHERE 1=1 AND `date` < ? AND `handle_id` = ? AND `text` IS NOT NULL;", (end, handle))
                count += c.fetchone()[0]
        return count 


    def messagesFromNumber(self, num):
        
        """ Returns a list of all the messages from a given number. """
        
        if not self._built:
            self._build()
        handles = [handle for handle, number in self._handleDict.items() if number == num]
        messages = []
        c = self._connSMS.cursor()
        for handle in handles:
            c.execute("SELECT `handle_id`, `date`, `text`, `is_sent` FROM `message` WHERE 1=1 AND `handle_id` LIKE " + str(handle) + " ORDER BY `date`")
            rows = c.fetchall()
            for mes in rows:
                message = Message(mes[2])
                message.number = num
                message.timestamp = self._intToDate(mes[1])
                if mes[3] == 1:
                    message.sent = True
                else:
                    message.sent = False
                messages.append(message)
        return messages

    def countFromNumber(self, num):
        
        """ Returns the number of messages from a given number. """
        
        if not self._built:
            self._build()
        return self._countDict[num]

    def wordsFromNumber(self, num):
        
        """ Returns the total number of words from a given number. """
        
        if not self._built:
            self._build()
        return self._wordDict[num]

    def _intToDate(self, integer):
        
        """ Converts a time in interger format (seconds since January First 2001) to a datetime object. """
        # TODO Fix so it doesn't need a manual timezone offset.
        
        delta = datetime.timedelta(seconds = integer)
        date = datetime.datetime(2001, 1, 1)
        timezoneoffset = datetime.timedelta(hours = 5)
        return (date + delta - timezoneoffset)

    def _dateToInt(self, date):
        
        """ Converts a datetime object to integer format. """
        
        timezoneoffset = datetime.timedelta(hours = 5)
        delta = date + timezoneoffset - datetime.datetime(2001, 1, 1)
        return int(delta.total_seconds())

    def _getHandlesFromNumber(self, num):
        
        """ Returns a list of handles that correspond to a given number. """
        
        handles = [handle for handle, number in self._handleDict.items() if number == num]
        return handles
       

class Message():

    """ Message ADT """

    def __init__(self, text):
        
        """ Creates the instance variables """
        
        # Canonicalized Number (+15555555555)
        self.number = None
        # Timestamp: Datetime object.
        self.timestamp = None
        # Text
        self.text = text
        # Sent boolean
        self.sent = None
    
    def getWords(self):
        
        """ Returns the number of words in a given message. """
        
        if self.text:
            return len(re.findall("[a-zA-Z_]+", self.text))
        else:
            return 0

