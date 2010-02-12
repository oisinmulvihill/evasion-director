<%doc>
	Site Root Page (c) Oisin Mulvihill, All rights reserved.
</%doc>
<%inherit file="base.mako"/>

## Body 
<h2>Please log in</h2>
<form action="${c.url_for('/login_handler', came_from=c.came_from, __logins=c.login_counter)}" method="POST">
  <label for="login">Username:</label><input type="text" id="id_username" name="login"/><br/>
  <label for="password">Password:</label><input type="password" id="id_password" name="password" />
  <input id="login-btn" type="submit" value="Login" />
</form>

