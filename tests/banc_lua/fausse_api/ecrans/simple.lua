-- FAUX ecran quelconque (screen_front, holomap_screen, screen_veh_top_m...) : begin() -> begin_load(), update() renvoie une valeur.
function update(screen_w, screen_h, tick_fraction, delta_time)
	return "simple_ok", screen_w
end

function begin() begin_load() end
