# coding=utf-8
import re
import queue as Queue
import threading
from gevent.pool import Pool


import requests
from mongoengine import NotUniqueError

from models import Proxy,Article
from config import PROXY_REGEX, PROXY_SITES
from remove_unavailable_proxy import check_proxy
from gevent import monkey; monkey.patch_all()
from search_result_with_lock import use_gevent_with_queue


def save_proxies(url):
    proxies = []
    try:
        # if url == 'http://www.kuaidaili.com/free':
        #     import pdb;
        #     pdb.set_trace()
        res = requests.get(url)

    except requests.exceptions.RequestException:
        return False
    addresses = re.findall(PROXY_REGEX, res.text)
    for address in addresses:
        proxy = Proxy(address=address)
        try:
            proxy.save()
        except NotUniqueError:
            pass
        else:
            proxies.append(address)
    return proxies


def cleanup():
    Proxy.drop_collection()
    Article.drop_collection()


def save_proxies_with_queue2(in_queue, out_queue):
    while True:
        url = in_queue.get()
        # import pdb; pdb.set_trace()
        rs = save_proxies(url)
        out_queue.put(rs)
        in_queue.task_done()  # 队列完成发送信号


def append_result(out_queue, result):
    while True:
        rs = out_queue.get()
        if rs:
            result.extend(rs)
        out_queue.task_done()


def use_thread_with_queue2():
    cleanup()
    # in_queue = Queue.Queue()
    # out_queue = Queue.Queue()
    #
    # for i in range(5):
    #     t = threading.Thread(target=save_proxies_with_queue2,
    #                          args=(in_queue, out_queue))
    #     t.setDaemon(True)
    #     t.start()
    #
    # for url in PROXY_SITES:
    #     in_queue.put(url)
    #
    # result = []
    #
    # for i in range(5):
    #     t = threading.Thread(target=append_result,
    #                          args=(out_queue, result))
    #     t.setDaemon(True)
    #     t.start()
    #
    # in_queue.join()
    # out_queue.join()

    addresses = []

    # mogu_key = ""
    # res = requests.get(mogu_key)
    # addresses = res.json()['msg']

    for address in addresses:
        proxy = Proxy(address=address['ip']+':'+address['port'])
        try:
            proxy.save()
        except NotUniqueError:
            pass


    pool = Pool(10)
    pool.map(check_proxy, Proxy.objects.all())
    print(len(addresses))
    print(Proxy.objects.count())


def save_proxies_with_queue(queue):
    while 1:
        url = queue.get()
        save_proxies(url)
        queue.task_done()  # 队列完成发送信号


def use_thread_with_queue():
    cleanup()
    queue = Queue.Queue()

    for i in range(5):
        t = threading.Thread(target=save_proxies_with_queue, args=(queue,))
        t.setDaemon(True)
        t.start()

    for url in PROXY_SITES:
        queue.put(url)

    queue.join()


if __name__ == '__main__':
    use_thread_with_queue2()
    use_gevent_with_queue()
