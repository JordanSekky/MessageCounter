#!/usr/bin/env python3
# encoding: utf-8
import sqlite3
import operator
import os
import re
import sys
import datetime

class reader():

    """Docstring for reader. """

    def __init__(self):
        """TODO: to be defined1.

        :path: TODO

        """
        self._connSMS = None
        self._connAdd = None
        self._handleDict = {}
        self._wordDict = {}
        self._countDict = {}
        self._built = False

    def lastDate(self):
        c = self._connSMS.cursor()
        c.execute("SELECT `date` FROM `message`  ORDER BY `date` DESC LIMIT 0, 1;")
        mostrecent = c.fetchone()[0]
        return self._intToDate(mostrecent)

    def getNameFromNumber(self, number):
        """TODO: Docstring for getNameFromNumber.

        :number: TODO
        :returns: TODO

        """
        lastfour = str(number)[-4:]
        a = self._connAdd.cursor()
        a.execute("SELECT multivalue_id FROM `ABPhoneLastFour` WHERE 1=1 AND `value` LIKE '" + lastfour + "' ORDER BY `value` DESC LIMIT 0, 50000;")
        lastFourRow = a.fetchone()
        # print(lastFourRow)
        if lastFourRow is None:
            return str(number)
        multiId = lastFourRow[0]
        a.execute("SELECT record_id FROM `ABMultiValue` WHERE 1=1 AND `UID` LIKE '" + str(multiId) + "' ORDER BY `_rowid_` ASC LIMIT 0, 50000;")
        personId = a.fetchone()[0]
        a.execute("SELECT First, Last FROM `ABPerson` WHERE 1=1 AND `ROWID` LIKE '" + str(personId) + "' ORDER BY `_rowid_` ASC LIMIT 0, 50000;")
        personRow = a.fetchone()
        if personRow[1] is not None:
            name = personRow[0] + " " + personRow[1].split()[0]
        else:
            name = personRow[0]
        return name

    def getNumberFromHandle(self, handle):
        """TODO: Docstring for getHandleNumber.
        :returns: TODO

        """
        if handle in self._handleDict.keys():
            return self._handleDict[handle]
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



    def addAddressBook(self, path):
        assert os.path.exists(path)
        self._connAdd = sqlite3.connect(path)

    def addSMSDatabase(self, path):
        """TODO: Docstring for addSMSDatabase.

        :path: TODO
        :returns: TODO

        """
        assert os.path.exists(path)
        self._connSMS = sqlite3.connect(path)
        self._connSMS.create_function("words", 1, reader.wordcount)

    def _build(self):
        self._buildHandleDict()
        self._buildOthers()
        self._built = True
        
    def _buildHandleDict(self):
        """TODO: Docstring for getListOfNumbers.
        :returns: TODO

        """
        c = self._connSMS.cursor()
        c.execute("SELECT DISTINCT `handle_id` FROM `message`  ORDER BY `handle_id`;")
        handleList = c.fetchall()
        for handletuple in handleList:
            handle = handletuple[0]
            if handle == 0:
                continue
            self.getNumberFromHandle(handle)

    def _buildOthers(self):
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
        c = self._connSMS.cursor()
        c.execute("SELECT COUNT(text) FROM `message`")
        return c.fetchone()[0]
    
    def getListOfNumbers(self):
        """TODO: Docstring for getListOfNumbers.
        :returns: TODO

        """
        if not self._built:
            self._build()
        return set(self._handleDict.values())

    def messagesOnDate(self, date, number = None):
        """TODO: Docstring for getNumOnDate.

        :number: TODO
        :returns: TODO

        """
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
        if not self._built:
            self._build()
        end = self._dateToInt(datetime.datetime.combine(date, datetime.time(0)) + datetime.timedelta(days = 1))
        c = self._connSMS.cursor()
        count = 0
        if not number:
            c.execute("SELECT COUNT(*) FROM `message` WHERE `date` < " + str(end) + " AND `text` IS NOT NULL;")
            count = c.fetchone()[0]
        else:
            # print(self._getHandlesFromNumber(number))
            for handle in self._getHandlesFromNumber(number):
                c.execute("SELECT COUNT(*) FROM `message` WHERE 1=1 AND `date` < ? AND `handle_id` = ? AND `text` IS NOT NULL;", (end, handle))
                count += c.fetchone()[0]
        return count 


    def messagesFromNumber(self, num):
        if not self._built:
            self._build()
        handles = [handle for handle, number in self._handleDict.items() if number == num]
        messages = []
        c = self._connSMS.cursor()
        for handle in handles:
            c.execute("SELECT `handle_id`, `date`, `text` FROM `message` WHERE 1=1 AND `handle_id` LIKE " + str(handle))
            rows = c.fetchall()
            for mes in rows:
                message = Message()
                message.number = num
                message.timestamp = self._intToDate(mes[1])
                message.text = mes[2]
                messages.append(message)
        return messages

    def countFromNumber(self, num):
        if not self._built:
            self._build()
        return self._countDict[num]

    def wordsFromNumber(self, num):
        if not self._built:
            self._build()
        return self._wordDict[num]

    def _intToDate(self, integer):
        """TODO: Docstring for _intToDate.
        :returns: TODO

        """
        delta = datetime.timedelta(seconds = integer)
        date = datetime.datetime(2001, 1, 1)
        timezoneoffset = datetime.timedelta(hours = 5)
        return (date + delta - timezoneoffset)

    def _dateToInt(self, date):
        timezoneoffset = datetime.timedelta(hours = 5)
        delta = date + timezoneoffset - datetime.datetime(2001, 1, 1)
        return int(delta.total_seconds())

    def wordcount(text):
        if text:
            return len(re.findall("[a-zA-Z_]+", text))
        else:
            return 0

    def _getHandlesFromNumber(self, num):
        handles = [handle for handle, number in self._handleDict.items() if number == num]
        return handles
       

class Message():

    """Docstring for Message. """

    def __init__(self, text):
        """TODO: to be defined1. """
        # Canonicalized Number
        self.number = None
        # Timestamp
        self.timestamp = None
        # Text
        self.text = text
    
    def getWords(self):
        """TODO: Docstring for getWords.
        :returns: TODO

        """
        if self.text:
            return len(re.findall("[a-zA-Z_]+", self.text))
        else:
            return 0

