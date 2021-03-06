import xlwt
from rest_framework.decorators import action
from django.shortcuts import HttpResponse
from io import BytesIO
from urllib import parse


class ExportModelMixin(object):

    @action(methods=["get"], detail=False)
    def export(self, request, *args, **kwargs):
        assert hasattr(self, "export_class"), (
            "'%s' should either include a `export_class` attribute, "
            % self.__class__.__name__
        )
        self.response = HttpResponse(content_type='application/vnd.ms-excel')
        excel_name = self.get_excel_name()
        self.response['Content-Disposition'] = 'attachment;filename={0}.xls'.format(excel_name)
        self.wb = xlwt.Workbook(encoding='utf-8')
        self.render_content()
        return self.response

    def get_excel_name(self):
        assert hasattr(self.export_class, "excel_name"), (
                "'%s' should either include a `excel_name` attribute, "
                % self.export_class.__name__
        )
        if isinstance(self.export_class.excel_name, str):
            return parse.quote(self.export_class.excel_name)
        raise ValueError("excel_name must be string")

    def render_content(self):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        header = self.export_class.header
        labels = self.export_class.labels if hasattr(self.export_class, "labels") else {}

        assert isinstance(labels, dict), (
                "'labels' must be dict type"
        )

        data = [[labels.get(column, column) for column in header]]
        for item in serializer.data:
            data.append([item.get(column) for column in  header])

        sheet_prd = self.wb.add_sheet('sheet1')
        for row_index, row in enumerate(data):
            for column_index, column in enumerate(row):
                sheet_prd.write(row_index, column_index, column)

        output = BytesIO()
        self.wb.save(output)
        output.seek(0)
        self.response.write(output.getvalue())

# 以下为示例
class SalesExport:
    # 表格的列 有序
    header = ["id","name", "period", "valid_order_count", "status", "started_at", "ended_at"]
    # 表格名称 必写
    excel_name = "秒杀周期"
    # 字段对应的表头名字, 非必写
    labels = {
        'name': '名字',
        'period': '周期'
    }


class SalesActivityScheduleViewSet(ExportModelMixin,
                                   GenericViewSet):
    """
    秒杀预设周期
    """
    queryset = SalesActivitySchedule.objects.all()
    serializer_class = SalesActivityScheduleListSerializer
    # 必写
    export_class = SalesExport

    def get_serializer_class(self):
        if self.action == "export":
            return SalesActivityScheduleListSerializer
        return self.serializer_class

