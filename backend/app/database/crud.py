#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
@Author: GnepGnaz
@Time: 2024/1/26 10:57
@File: base.py
@Software: qing_language

如果出现了mysql错误：pymysql.err.OperationalError: (1205, 'Lock wait timeout exceeded; try restarting transaction') 错误
请执行下面两句话，进行会话kill
select * from information_schema.innodb_trx;
kill XXXX

接口中注意silence参数要使用object 传参的方式
"""

from typing import Dict, Generic, TypeVar, Type, Union, Tuple
import re
from datetime import datetime
from typing import List

from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import Session

from app.database.error import MysqlError, APIParaError
from .base import Base as TableBase
from sqlalchemy import desc, asc
from typing import Any
import time
from sqlalchemy.dialects.mysql import insert
import operator
from functools import reduce


def _decorate_excepthon(origin_func):
    """
    目前主要用于数据更新和数据插入的异常拦截
    :param origin_func:
    :return:
    """
    def wrapper(*args, **kw):
        # 需要对参数的顺序进行唯一化调整
        try:
            return origin_func(*args, **kw)
        except IntegrityError as e:
            if kw and "silence" in kw and kw.get("silence"):
                return None
            err_str = e.orig.args[1]
            if e.orig.args[0] == 1452:
                # err_str='Cannot add or update a child row: a foreign key constraint fails (`atom`.`user_manage`, CONSTRAINT `users_ibfk_1` FOREIGN KEY (`organization_id`) REFERENCES `organization` (`id`))'
                if err_str.startswith("Cannot add or update a child row: a foreign key constraint fails"):
                    print("外键约束错误")  # XXX 约束XXX
                    a = re.compile(
                        "[\w\W]+?\(`(?P<database>\w+?)`\.`(?P<table_child>\w+?)`, CONSTRAINT `\w+?` FOREIGN KEY \(`(?P<table_child_seg>\w+?)`\) REFERENCES `(?P<table_parent>\w+?)` \(`(?P<table_parent_seg>\w+?)`\)\)")
                    regMatch = a.match(err_str)
                    if regMatch:
                        result = regMatch.groupdict()
                        print(result)
                        raise MysqlError(
                            "数据录入错误",
                            data={"orig": e.orig.args, "message": f"外键约束错误({result['table_parent']}.{result['table_parent_seg']}可能不存在)",
                                  "table": result.get("table_child", ""),
                                  "segment": result.get("table_child_seg", ""),
                                  })
            elif e.orig.args[0] == 1062:  # 唯一字段检查
                a = re.compile(
                    "Duplicate entry '[\w\W]+' for key '(?P<table_child_seg>\w+?)'")
                regMatch = a.match(err_str)
                if regMatch:
                    result = regMatch.groupdict()
                    raise MysqlError(
                        "数据录入错误",
                        data={"orig": e.orig.args, "message": f"表中已经存在{result['table_child_seg']}",
                              "table": result.get("table_child", ""),
                              "segment": result.get("table_child_seg", ""),
                              })
            else:
                raise (e)
        except DataError as e:
            # pymysql.err.DataError: (1406, "Data too long for column 'group' at row 1")
            err_str = e.orig.args[1]
            if e.orig.args[0] == 1406:  # 唯一字段检查
                a = re.compile(
                    "Data too long for column '(?P<table_child_seg>\w+?)' at[\w\W]+?")
                regMatch = a.match(err_str)
                if regMatch:
                    table_child_seg = regMatch.groupdict().get("table_child_seg")
                    raise MysqlError(f'数据更新失败', data={"orig": e.orig.args, "message": f"{table_child_seg}字段长度过长。长度为{len(e.params.get(table_child_seg,''))}",
                                                      "table": "",
                                                      "segment": table_child_seg,
                                                      })
        finally:
            args[0].session.commit()  # 一定要加这句话，否则可能会导致trx_mysql_thread

    return wrapper


ModelType = TypeVar("ModelType", bound=TableBase)


class BaseOp(Generic[ModelType]):
    """
    sqlalchemy 的基本的增删改查

    关键词查找： https://www.cnblogs.com/kaerxifa/p/13476317.html
    忽略大小写： https://www.cnblogs.com/shengulong/p/9521598.html

    Generic[] 用于编程的时候的类型提示，非常好用。有时候父类是不知道子类要返回的具体的示例字段的。
    尤其是多个mysql 操作表，继承同一个父类，使用父类中的find_one 方法，这时候，父类不知道子类的实例是哪一个的。
    """

    def __init__(self, session: Session, model: Type[ModelType]):
        self.model = model
        self.session = session
        self._select_segs = []

    def make_filter_para(self, *args, **kw):
        """
        把 filter_by 或者 filter 的参数统一转化为filter 参数。要求：model 必须是默认的model
        :param args:
        :param kw:
        :return:
        """
        filter_para = [*args]
        for k in kw:
            filter_para.append(getattr(self.model, k) == kw[k])
        return filter_para

    def make_query(self, *args, **kw):
        if len(args) == 0:
            if len(self._select_segs):
                return self.session.query(*self._select_segs).filter_by(**kw)
            else:
                return self.session.query(self.model).filter_by(**kw)
        if len(self._select_segs):
            return self.session.query(*self._select_segs).filter(*self.make_filter_para(*args, **kw))
        else:
            return self.session.query(self.model).filter(*self.make_filter_para(*args, **kw))

    def find_one(self, *args, **kw) -> ModelType:
        return self.make_query(*args, **kw).first()

    def set_select_segs(self, *segs):
        """
        有的表格字段过多，通过这个进行设置返回值字段限制
        :param segs:
        :return:
        """
        self._select_segs = segs
        return self

    def find(self, *args, page_index: int = 0, page_size=0, sort_by=None, is_desc=True, fields=None, **kw) -> Union[
            List[ModelType], Tuple[int, List[ModelType]]]:
        """
        :param args:
        :param page_index:
        :param page_size:
        :param sort_by:  是必传的
        :param is_desc:
        :param kw:
        :return:
        """
        order_by = None
        query = self.make_query(*args, **kw)
        if fields:
            query = query.with_entities(*fields)
        if sort_by:
            if isinstance(sort_by, str):
                if "." in sort_by:
                    para_list = sort_by.split(".")
                    obj = getattr(self.model, para_list[0], None)
                    if not obj:
                        raise APIParaError("排序参数错误")
                    for item in para_list[1:]:
                        obj = obj[item]
                    order_by = obj.desc() if is_desc else obj.asc()
                else:
                    order_by = desc(sort_by) if is_desc else asc(sort_by)
            else:
                order_by = sort_by

        if page_size and page_index:
            if page_size == -1:
                return query.count(), query.order_by(order_by).all() if sort_by else query.all()
            else:
                if (query.count() / page_size) <= (page_index-1):
                    return 1, query.count(), query.order_by(order_by).offset(page_size * 0).limit(page_size).all() if sort_by else query.offset(page_size * 0).limit(page_size).all()
                else:
                    return page_index, query.count(), query.order_by(order_by).offset(page_size * (page_index - 1)).limit(page_size).all() if sort_by else query.offset(page_size * (page_index - 1)).limit(page_size).all()
        else:
            return query.order_by(order_by).all() if sort_by else query.all()

    def distinct(self, seg, *criterion, page_index: int = 0, page_size=0, sort_by=None, is_desc=True, **kw) -> Union[List[str], Tuple[int, List[str]]]:
        if len(criterion) == 0:
            query = self.session.query(seg).filter_by(**kw)
        else:
            query = self.session.query(seg).filter(
                *self.make_filter_para(*criterion, **kw))

        order_by = None
        if sort_by:
            if isinstance(sort_by, str):
                if "." in sort_by:
                    para_list = sort_by.split(".")
                    obj = getattr(self.model, para_list[0], None)
                    if not obj:
                        raise APIParaError("排序参数错误")
                    for item in para_list[1:]:
                        obj = obj[item]
                    order_by = obj.desc() if is_desc else obj.asc()
                else:
                    order_by = desc(sort_by) if is_desc else asc(sort_by)
            else:
                order_by = sort_by
        query = query.order_by(order_by) if sort_by else query

        if page_index and page_size:
            start = page_size * (page_index - 1)
            data = query.offset(page_size * (page_index - 1)
                                ).distinct(seg)[start:start + page_size]  # [(),()]
            # data_list = [list(item) for item in data]  # 兼容 py3.9
            data_list = [dict(zip(item.keys(), item)) for item in data]
            return data_list
            # return query.distinct(seg).count(), reduce(operator.add, data_list or [[]])

        data = query.distinct(seg).all()
        # [(),()] [sqlalchemy.engine.row.Row,sqlalchemy.engine.row.Row]
        # data_list = [list(item) for item in data]  # 兼容 py3.9
        # [{},{}] [sqlalchemy.engine.row.Row,sqlalchemy.engine.row.Row]
        data_list = [dict(zip(item.keys(), item)) for item in data]
        # return reduce(operator.add, data_list or [[]])
        return data_list

    def count(self, *criterion, **kw) -> int:
        return self.make_query(*criterion, **kw).count()

    @_decorate_excepthon
    def add_from_model(self, model_instance: ModelType, silence: bool = False) -> ModelType:
        # 添加到session
        self.session.add(model_instance)
        # 提交
        self.session.commit()
        self.session.refresh(model_instance)
        return model_instance
    
    @_decorate_excepthon
    def add_all_from_model(self, model_instances: List[ModelType], silence: bool = False) -> ModelType:
        # 添加到session
        self.session.add_all(model_instances)
        # 提交
        self.session.commit()
        return model_instances

    @_decorate_excepthon
    def bulk_insert(self, mappings: List[Dict], return_ids=False):
        """
        批量插入，如果插入不进去就报错
        :param mappings:
        :return:
        """
        
        if not return_ids:
            self.session.bulk_insert_mappings(self.model, mappings)
            self.session.commit()
        else:
            with self.session.begin_nested():
                self.session.bulk_insert_mappings(self.model, mappings)
                new_ids = [row.id for row in self.session.query(self.model).order_by(self.model.id.desc()).limit(len(mappings))][::-1]
            self.session.commit()
            return new_ids

    # def remove_from_model(self,model_instance:ModelType)->ModelType:
    #     # 添加到session
    #     self.session.delete(model_instance)
    #     # 提交
    #     self.session.commit()
    #     self.session.refresh(model_instance)
    #     return model_instance

    def remove(self, *criterion, **kw):
        query = self.make_query(*criterion, **kw)
        query.delete(synchronize_session=False)
        self.session.commit()

    def bulk_insert_ignore(self, mappings: List[Dict]):
        """
        有的话就忽略，没有的话就添加
        :param mappings:
        :return:
        """
        if len(mappings) == 0:
            return
        self.session.execute(
            self.model.__table__.insert().prefix_with(" ignore"),
            mappings
        )
        self.session.commit()

    def _process_on_duplicate_key_update(self, data: List[Dict], upsert_col: List[str] = None):
        process_data = []
        if not upsert_col:
            upsert_col = list(data[0].keys())
        insert_stmt = insert(self.model)
        upsert_para = {}
        error_flag = False
        for col_name in upsert_col:
            try:
                upsert_para[col_name] = getattr(insert_stmt.inserted, col_name)
            except Exception:
                error_flag = True
        if error_flag:  # 需要筛选data 中的某些数据
            for item in data:
                _item = {}
                for k in item:
                    if k in upsert_para:
                        _item[k] = item[k]
                process_data.append(_item)
        else:
            process_data = data
        return insert_stmt.values(process_data).on_duplicate_key_update(
            **upsert_para
        )

    def bulk_insert_update(self, mappings: List[Dict], upsert_col: List[str] = None):
        """
        语法实现： INSERT INTO example (id,a,b) VALUES (1,2,3),(4,5,6) ON DUPLICATE KEY UPDATE a=VALUES(a),b=VALUES(b)
        有就更新，没有就添加
        :param mappings:
        :param upsert_col:
        :return:
        """
        if len(mappings) == 0:
            return
        on_duplicate_key_stmt = self._process_on_duplicate_key_update(
            mappings, upsert_col)
        self.session.execute(on_duplicate_key_stmt)
        self.session.commit()

    def add_update(self, upsert_col: List[str] = None, **kw):
        """
        单条数据的插入：  有就更新,没有就添加
        Note: 可能导致主键跟着修改
        :return:
        """
        on_duplicate_key_stmt = self._process_on_duplicate_key_update([
                                                                      kw], upsert_col)
        self.session.execute(on_duplicate_key_stmt)
        self.session.commit()

    def add_update_with_result(self, pk_value, pk_seg="id", **kw):
        """
        先查询是否有相关的数据，如果是插入，返回True, 更新，返回False
        :param pk_value:
        :param pk_seg:
        :param kw:
        :return: insert :True  update:False
        """
        r = False if self.find_one(**{pk_seg: pk_value}) else True
        self.add_update(**kw)
        return r

    def bulk_update(self, mappings: List[Dict]):
        """
        只用于批量更新，不会插入数据
        :param mappings:
        :return:
        """
        if len(mappings) == 0:
            return
        self.session.bulk_update_mappings(self.model, mappings)
        self.session.commit()

    def update_from_model(self, model_instance: ModelType, silence: bool = False) -> ModelType:
        return self.add_from_model(model_instance, silence=silence)

    @_decorate_excepthon
    def update(self, *criterion, usd_set: Dict, **kw):
        """
        用于根据某些条件，批量更新某些字段
        :param usd_set:  参数用于数据的更新。其他两个参数用于条件的筛选
        :param criterion:
        :param kw:
        :return:
        """
        self.make_query(*criterion, **kw).update(usd_set,
                                                 synchronize_session=False)
        self.session.commit()

    @staticmethod
    def get_table_data(base_query, base_filters: List, time_field, keyword_field, page_index: int = 1,
                       page_size: int = 10,
                       since: int = 0, until: int = 0, keyword: str = "", sort_by="created_t", is_desc=True, return_query=False) -> (int, Any):
        my_filters = base_filters
        if keyword and keyword.strip():
            my_filters.append(keyword_field.like(f"%{keyword.strip()}%"))
        if since:
            until = int(time.time()) if not until else until
            my_filters += [time_field >= since, time_field <= until]
            my_filter = base_query.filter(*my_filters)
            total = my_filter.count()
            # 热度的话，暂时定义为 repost_num、comment_num、like_num 三个值的降序排列
            my_filter = my_filter.order_by(
                desc(sort_by) if is_desc else asc(sort_by))

        else:  # 按照页获取数据
            my_filter = base_query.filter(*my_filters)
            total = my_filter.count()
            my_filter = my_filter.order_by(desc(sort_by) if is_desc else asc(sort_by)).offset(
                page_size * (page_index - 1)).limit(page_size)
        return total, my_filter.all() if not return_query else my_filter
