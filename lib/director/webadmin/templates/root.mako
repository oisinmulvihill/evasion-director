<%doc>
	Site Root Page
</%doc>
<%inherit file="base.mako"/>

## Head Resources
<%def name="heading()">
    <style type="text/css">
##        @import url("${h.url_for('/css/??.css')}");
    </style>
</%def>

## Body 
<div id="content">
    % if not c.modules:
        <h2>No modules to load</h2>
        <div>
            <em>None set in the director configuration?</em>
        </div>
    % endif
    
    % for m in c.modules:
        Module: ${ str(m) }
    % endfor
</div>

<%def name="foot()">
</%def>

