<div class="floor_map_cont">
    <img width="${width}" height="${height}" class="floor_map"
         src="/assets/pages/floors/${filename}.png" />
    <map>
        % for apartment in entity.apartments:
        <area shape="poly"
              coords="${apartment.area_coords(floor_dir=svg_dir,
                                              size=(width, height),
                                              sort_by=sort_by,
              reverse=reverse)}"
              alt="${apartment.get_id(apt_id_pattern)}" />
        % endfor
    </map>
</div>