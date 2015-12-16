<%inherit file="layout.mako"/>
<%def name="title()">Проекты</%def>
<table class="table table-striped tab-pane">
    <thead>
    <tr>
        <th>ID</th>
        <th>Название</th>
        <th>Лотов в базе</th>
        <th>Действия</th>
    </tr>
    </thead>
    <tbody>
        %for project in projects:
            <tr id="${project.title}" class="apt">
                <td>${project.title}</td>
                <td></td>
                <td>${len(project.fetch_apartments())}</td>
                <td>
                    <a style="margin-right:.5em" title="просмотреть лоты"
                       class="btn pull-right btn-mini"
                       href="${request.route_path('project', title=project.title)}">
                        <i class="icon-th-list"></i>
                        лоты
                    </a>
                    <a style="margin-right:.5em" title="Скачать xls"
                       class="btn pull-right btn-mini"
                       href="${request.route_path('xls', title=project.title)}">
                        <i class="icon-download"></i>
                        xls
                    </a>
                </td>
            </tr>
        %endfor
    </tbody>
</table>