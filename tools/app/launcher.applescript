-- Social Empires launcher: starts the local server, opens the game in the default browser,
-- and stops the server when you quit the app (Cmd+Q or Dock > Quit).
property projectDir : "__PROJECT_DIR__"
property gameURL : "http://127.0.0.1:5050/"

on serverIsUp()
	try
		do shell script "/usr/sbin/lsof -nP -iTCP:5050 -sTCP:LISTEN -t"
		return true
	on error
		return false
	end try
end serverIsUp

on openGame()
	-- wait up to 60 s for the server (a fresh start takes a few seconds)
	repeat 120 times
		if my serverIsUp() then exit repeat
		delay 0.5
	end repeat
	if my serverIsUp() then
		open location gameURL
	else
		display alert "Social Empires" message "The server did not start. See logs/server.log in the project folder." as critical
	end if
end openGame

on run
	if not my serverIsUp() then
		do shell script "cd " & quoted form of projectDir & " && mkdir -p logs && (nohup ./start.sh > logs/server.log 2>&1 &) > /dev/null 2>&1"
	end if
	my openGame()
end run

on reopen
	-- clicking the Dock icon again re-opens the game page
	my openGame()
end reopen

on idle
	return 30
end idle

on quit
	try
		do shell script quoted form of projectDir & "/stop.sh"
	end try
	continue quit
end quit
