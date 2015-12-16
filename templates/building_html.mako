<div id="building_map_cont">
    <img width="${width}" height="${height}" id="building_map"
         src="/assets/pages/buildings/1-${entity.number}.png" />
    <map>
        % for section in entity.sections:

        <area shape="poly" coords="${section.area_coords(buildings_dir=svg_dir,
                                                         size=(width, height))}"
              alt="1-${section.building_number}-${section.number}" />
        % endfor
    </map>
</div>