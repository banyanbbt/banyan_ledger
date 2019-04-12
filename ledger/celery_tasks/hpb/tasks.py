import datetime
import hashlib
import logging
import time

import pymysql
import requests

from celery_tasks.main import app
from celery_tasks import settings

logger = logging.getLogger('django')


def get_access_token():
    url = settings.BASE_URL

    data = {
        "txnCode": settings.HPB_TOKEN_TXNCODE,
        "appId": settings.HPB_APPID,
        "appKey": settings.HPB_APPKEY
    }

    response = requests.post(url=url, json=data)

    return response.json()["data"]["accessToken"]


def get_conn():
    return pymysql.connect(
        host=settings.HOST,
        port=settings.PORT,
        user=settings.USER,
        password=settings.PASSWORD,
        db=settings.DATABASE,
        charset=settings.CHARSET
    )


def get_json():
    now_time = datetime.datetime.now().strftime('%Y%m%d%H')
    before_time = (datetime.datetime.now() + datetime.timedelta(hours=-1)).strftime('%Y%m%d%H')
    time_range = before_time + "-" + now_time

    conn = get_conn()
    cursor = conn.cursor()

    now_day = datetime.datetime.now().strftime('%Y-%m-%d')
    now_hour = datetime.datetime.now().strftime('%H:00:00')
    before_hour = (datetime.datetime.now() + datetime.timedelta(hours=-1)).strftime('%H:00:00')

    params = [now_day, before_hour, now_hour]
    sql = "select  account ,group_concat(distinct product),count(request_count) as request_count,count(bill_count) as success_count from bill_hourly where request_count > 0 and day_at = %s and time_at > %s and time_at < %s group by account"

    cursor.execute(sql, params)
    result_list = cursor.fetchall()

    if len(result_list) == 0:
        return result_list

    account_list = []
    for result in result_list:
        data = {
            "account": 'BC' + hashlib.md5(result[0][1:].encode()).hexdigest(),
            "product": result[1].split(","),
            "request_count": result[2],
            "success_count": result[3],
            "time_range": time_range
        }
        account_data = {
            "account": result[0],
            "data": data
        }
        account_list.append(account_data)

    json_list = []
    access_token = get_access_token()
    now_date = datetime.datetime.now().strftime('%Y%m%d')

    for temp in account_list:
        request_json = {
            "txnCode": settings.HPB_REQUEST_TXNCODE,
            "txnNo": settings.HPB_TXNNO + datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            "accessToken": access_token,
            "tradeDate": now_date,
            "licenseId": settings.HPB_LICENSE_ID,
            "appKey": settings.HPB_APPKEY,
            "appId": settings.HPB_APPID,
            "fromAccount": settings.HPB_FROM_ACCOUNT,
            "fromAccountPwd": settings.HPB_FROM_ACCOUNT_PWD,
            "metaData": str(temp["data"])
        }

        # 组织account和请求参数
        json_account = {
            "account": temp['account'],
            "request_json": request_json
        }

        json_list.append(json_account)

        # txnNo流水号唯一，精准到秒
        time.sleep(1)

    cursor.close()
    conn.close()
    return json_list


@app.task()
def post_hpb():
    url = settings.TARGET_URL
    # 获取json列表,
    json_list = get_json()

    if len(json_list) == 0:
        logger.info("该时间段账户申请记录为null")
        return

    conn = get_conn()
    cursor = conn.cursor()

    # 遍历列表，发送post请求
    for json_account in json_list:

        # 发送前保留metaData明文数据
        meta_data = json_account['request_json']['metaData']
        # logger日志输出参数
        meta_obj = eval(meta_data)

        # 获取请求json
        request_json = json_account['request_json']
        # md5加密post请求中的metaData
        request_json["metaData"] = hashlib.md5(meta_data.encode()).hexdigest()

        response = requests.post(url=url, json=request_json)
        rescontent = response.json()

        if rescontent['rspCode'] != '0':
            logger.info("接口请求失败,rspMsg:%s,account:%s,time_range:%s" % (
                rescontent['rspMsg'], json_account['account'], meta_obj['time_range']))

        txn_no = request_json['txnNo']
        create_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        trade_hash = ""
        if rescontent['rspCode'] == '0':
            trade_hash = rescontent['data']['tradeHash']

        try:
            params = [txn_no, meta_data, trade_hash, create_at]
            sql = "insert into blockchain_ledger (txn_no, metaData, trade_hash, created_at) values (%s,%s,%s,%s)"
            cursor.execute(sql, params)
            conn.commit()
        except:
            logger.info("数据库写入错误,account:%s,time_range:%s" % (json_account['account'], meta_obj['time_range']))
            conn.rollback()

    cursor.close()
    conn.close()
