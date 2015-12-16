<%inherit file="layout.mako"/>
<%def name="title()">Проекты:{project.title}</%def>

%if len(project.quarters) is 1:
<ul id="building_tabs" class="nav nav-tabs">
        %for building in project.quarters[0].buildings:
            <li>
                <a href="#building_${building.number}" data-toggle="tab">
                    Корпус ${building.number}
                </a>
            </li>
        %endfor
</ul>
%else:
<ul id="quarter_tabs" class="nav nav-tabs">
        %for quarter in project.quarters:
            <li>
                <a href="#building_${quarter.number}" data-toggle="tab">
                    Очередь ${quarter.number}
                </a>
            </li>
        %endfor
</ul>
%endif