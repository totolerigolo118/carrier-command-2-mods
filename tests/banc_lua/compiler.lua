-- Compile un fichier Lua SANS l'executer (loadfile) : lua5.3 compiler.lua fichier.lua
-- Sortie : "OK" (code 0) ou le message d'erreur du compilateur (code 1).
local f, e = loadfile(arg[1])
if not f then
	io.write(e)
	os.exit(1)
end
io.write("OK")
