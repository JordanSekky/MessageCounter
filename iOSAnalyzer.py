#!/usr/bin/env python3
# encoding: utf-8
from iOSReader import *
import matplotlib.pyplot as plt
from clint.textui import progress

r = reader()
prefix = "Sechler"
numlines = 10
numdays = 365
r.addAddressBook(prefix + "/AddressBook/AddressBook.sqlitedb")
r.addSMSDatabase(prefix + "/sms/sms.db")
numberwords = []
for number in r.getListOfNumbers():
    words = r.wordsFromNumber(number)
    count = r.countFromNumber(number)
    numberwords.append((number, count, words, words // count))
sortedlist = sorted(numberwords, key = lambda item: item[1], reverse = True)[:numlines]
numberlist = [i[0] for i in sortedlist]
lastday = r.lastDate()
firstday = lastday - datetime.timedelta(days = numdays)
monthlinenums = []
curMonth = datetime.date(lastday.year, lastday.month, 1)
monthdict = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
while curMonth > firstday.date():
    # print((curMonth - firstday.date()).days)
    monthlinenums.append(((curMonth - firstday.date()).days, curMonth))
    if curMonth.month == 1:
        curMonth = datetime.date(curMonth.year - 1, 12, 1)
    else:
        curMonth = datetime.date(curMonth.year, curMonth.month - 1, 1)
# print(monthlinenums)
with progress.Bar(expected_size=numdays*numlines*2) as bar:
    count = 0
    bar.show(count)
    for number in numberlist:
        xlist = []
        ylist = []
        for i in range(numdays, -1, -1):
            date = lastday - datetime.timedelta(days = i)
            xlist.append(numdays-i)
            total = r.totalOnDate(date, number)
            ylist.append(total)
            count += 1
            bar.show(count)
        plt.plot(xlist, ylist, linewidth=2.0, label = r.getNameFromNumber(number))
        # print(r.getNameFromNumber(number))
    plt.ylabel('Number of Messages')
    plt.xlabel('Days since ' + firstday.isoformat()[:10])
    plt.legend([r.getNameFromNumber(number) for number in numberlist], loc=2)
    for line in monthlinenums:
        plt.axvline(x=line[0], ls='--')
        # plt.figtext(line[0]/numdays, 0.75, "Wtf")
        plt.annotate(monthdict[line[1].month], xy=(line[0] + 5, 15))
    fig = plt.gcf()
    fig.set_size_inches(18.5,10.5)
    fig.savefig(prefix + 'png.png',dpi=100)
    plt.clf()
    for number in numberlist:
        xlist = []
        ylist = []
        startdate = lastday - datetime.timedelta(days = numdays)
        enddate = startdate + datetime.timedelta(days = 5)
        for i in range(numdays//5, -1, -1):
            difference = r.totalOnDate(enddate, number) - r.totalOnDate(startdate, number)
            xlist.append(numdays//5 - i)
            ylist.append(difference // 5)
            startdate += datetime.timedelta(days = 5)
            enddate += datetime.timedelta(days = 5)
            count += 5
            bar.show(count)
        plt.plot(xlist, ylist, linewidth=2.0, label = r.getNameFromNumber(number))
        # print(r.getNameFromNumber(number))
    plt.ylabel('Number of Messages per day, 5 day polling')
    plt.xlabel('5 Days periods since ' + firstday.isoformat()[:10])
    plt.legend([r.getNameFromNumber(number) for number in numberlist], loc=2)
    for line in monthlinenums:
        plt.axvline(x=line[0]//5, ls='--')
        plt.annotate(monthdict[line[1].month], xy=(line[0]//5 + 1, 15))
    fig = plt.gcf()
    fig.set_size_inches(18.5,10.5)
    fig.savefig(prefix + 'slopes.png',dpi=100)
