# Explore tree package - Release 2

-----
## Version 0.0.1
* Bufix: Fix the problem of displaying the view for a link (This features was broken in the last release)
* Download the displayed data
* Download the main queried file
* Cache all the result files that can be accessed for the current node 

Modified files :
	. \explore_tree\ajax.py
	. \explore_tree\urls.py
	. \explore_tree\views.py
	. \explore_tree\api\navigation\operations.py
	. \explore_tree\api\models.py
	. \explore_tree\parser\query.py
	. (\explore_tree\parser\renderer.py)
	. \explore_tree\static\explore_tree\js\load_view.js
	. (\explore_tree\static\explore_tree\js\resize_tree_panel.js)
	. (\explore_tree\static\explore_tree\js\tree.js)
	. \explore_tree\templates\explore_tree\content.html
	. \templates\am\explore_tree_wrapper.html
	. \templates\am\landing_page.html
	. \mgi\models.py
	. \mgi\settings.py
	. \mgi\urls.py
	. \utils\json_parser\processview.py
	. \utils\xml_utils\projection.py

Added files :
	. \explore_tree\dicttoxml.py
	
	
-----
