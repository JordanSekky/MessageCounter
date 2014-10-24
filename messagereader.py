import sqlite3
import operator
import re
import sys

prefix = "Sechler"


endDict = {}
wordDict = {}
aveDict = {}

handleDict = {}

SORTER = endDict
NUM_ROWS = 10

def getHandleNumber(handle, conn):
    """TODO: Docstring for getHandleNumber.
    :returns: TODO

    """
    if handle in handleDict.keys():
        return handleDict[handle]
    else:
        d = conn.cursor()
        d.execute("SELECT `id` FROM `handle` WHERE 1=1 AND `ROWID` LIKE '" + str(handle) + "' ORDER BY `_rowid_` ASC LIMIT 0, 1;", )
        result = d.fetchone()
        if result is not None:
            handleDict[handle] = result[0]
            return result[0]
        else:
            handleDict[handle] = None
            return None

def getNameFromNumber(number, addconn):
    """TODO: Docstring for getNa meFromNumber.

    :number: TODO
    :returns: TODO

    """
    lastfour = number[-4:]
    a = addconn.cursor()
    a.execute("SELECT multivalue_id FROM `ABPhoneLastFour` WHERE 1=1 AND `value` LIKE '" + lastfour + "' ORDER BY `value` DESC LIMIT 0, 50000;")
    lastFourRow = a.fetchone()
    # print(lastFourRow)
    if lastFourRow is None:
        return number
    multiId = lastFourRow[0]
    a.execute("SELECT record_id FROM `ABMultiValue` WHERE 1=1 AND `UID` LIKE '" + str(multiId) + "' ORDER BY `_rowid_` ASC LIMIT 0, 50000;")
    personId = a.fetchone()[0]
    a.execute("SELECT First, Last FROM `ABPerson` WHERE 1=1 AND `ROWID` LIKE '" + str(personId) + "' ORDER BY `_rowid_` ASC LIMIT 0, 50000;")
    personRow = a.fetchone()
    # print(personRow)
    if personRow[1] is not None:
        name = personRow[0] + " " + personRow[1].split()[0]
    else:
        name = personRow[0]
    return name

def keywithmaxval(d):
    v=list(d.values())
    k=list(d.keys())
    return k[v.index(max(v))]

# for i in range(30):
#     printer = getHandleNumber(i)
#     if printer is not None:
#         print(printer[2])
def rank():
    conn = sqlite3.connect(prefix + "/sms/sms.db")
    addconn = sqlite3.connect(prefix + "/AddressBook/AddressBook.sqlitedb")
    c = conn.cursor()
    c.execute("SELECT text, handle_id FROM `message`  ORDER BY `_rowid_` ASC LIMIT 0, 50000;")

    # print("Totaling")
    for row in c.fetchall():
        handle = row[1]
        # print(handle)
        number = getHandleNumber(handle, conn)
        if number is None:
            continue
        if row[0] is not None:
            words = len(re.findall("[a-zA-Z_]+", row[0]))
        else:
            words = 0
        # words = len(row[0].split())
        if not number in endDict.keys():
            endDict[number] = 1
        else:
            endDict[number] += 1
        if not number in wordDict.keys():
            wordDict[number] = words
        else:
            wordDict[number] += words
    if SORTER == aveDict:
        for key in wordDict.keys():
            aveDict[key] = wordDict[key] / endDict[key]
    # print("Finished Totaling")

    string = ""
    for i in range(NUM_ROWS):
        # highestkey = keywithmaxval(endDict)
        highestkey = keywithmaxval(SORTER)
        if SORTER == wordDict:
            wordcount = wordDict.pop(highestkey)
            result = endDict[highestkey]
        elif SORTER == aveDict:
            wordcount = wordDict[highestkey]
            result = endDict[highestkey]
            aveDict.pop(highestkey)
        else:
            result = endDict.pop(highestkey)
            wordcount = wordDict[highestkey]
        # print(str(i + 1) + ": " + getNameFromNumber(highestkey) + ": " + str(result) + " messages, " + str(wordcount) + " words, " + str(wordcount//result) + " words/message")
        # print(highestkey[2] + ": " + str(endDict.pop(highestkey)))
        print("{:0>2d}: {: >19s}: {: >6,d} messages {: >6,d} words {: >2,d} words/message".format(i+1, getNameFromNumber(highestkey, addconn), result, wordcount, wordcount//result))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # print(sys.argv[1])
        prefix = sys.argv[1]
    if len(sys.argv) > 2:
        NUM_ROWS = int(sys.argv[2])
    if len(sys.argv) == 4:
        if sys.argv[3] == "message":
            SORTER = endDict
        elif sys.argv[3] == "word":
            SORTER = wordDict
        elif sys.argv[3] == "average":
            SORTER = aveDict
        else:
            print("Thats not a valid argument")
            sys.exit(0)

    rank()
