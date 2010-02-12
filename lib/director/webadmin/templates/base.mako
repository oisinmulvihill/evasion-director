<%doc> 
	Mako Base Master Template (c) Evasion Project. 
</%doc>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd"> 
<html>
    <head>
		${local.heading()}
		${self.heading()}
    </head>
    <body>
		<div id="header-pickout">&nbsp;</div>
		<div id="main">
			<div id="hd"> 
				${next.header()} 
			</div>
			
			<div id="bd" class="bottom-border">	
				<div id="content" class="bottom-border">
          			${next.body()} 
          			<div class="clear">&nbsp;</div>
				</div>
			</div>
		</div>

		<div id="ft"> 
			${local.footer()} 
		</div>
    </body>
</html>

<%def name="heading()">
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<meta name="author" content="EvasionProject" />
	<meta name="description" content="${ self.description() | trim }" />
	<meta name="keywords" content="${ self.keywords() | trim }" />
	<meta name="robots" content="all"/>
	<title>Evasion Project WebAdmin - ${ self.title() | trim }</title>
	<script type="text/javascript" src="${h.url_for('/js/jquery-min.js')}"></script> 
	<link rel='stylesheet' type="text/css" title='style-1' href="${ h.url_for('/css/site.css') }"/>	
</%def>

<%def name="header()">
	<div id="header">
	  <a href="${h.url_for('/')}">
	  </a>
	  ${self.menu()} 
	</div>
</%def>

## Things you can over to aid search engine rankings: 
##
<%def name="title()"></%def>
<%def name="keywords()"></%def>
<%def name="description()"></%def>

<%def name="menu()">

  <div id="logged-in-user">
    % if h.auth_details():
        Welcome ${ h.auth_details()['user'].name }
    %endif
  </div>

  <ul id="main-menu">
	%if h.is_authenticated():
    <li id="inactivetab"><a id="lnk-logout" title='Logout' href="${h.url_for('/logout_handler')}">
		Log Out</a>
	</li>
	%else:
    <li id="inactivetab"><a id="lnk-login" title='Login' href="${h.url_for('user-login')}">
		Log In</a>
	</li>
	%endif
  </ul>
</%def>

<%def name="submenu()">
</%def>


<%def name="footer()">
	<div id="footer">
		<div id="footer-content">
			${self.foot()}
		</div>
		<div id="site-details">
			WebAdmin v${h.siteversion}
		</div>
	</div>	
</%def>

<%def name="foot()"></%def>


