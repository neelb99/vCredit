function check(id){
	newfield = document.getElementById("studentroll");
	if (id.value=="student"){
		newfield.innerHTML = '<div class="form-group row"><div class="col-xs-5 col-md-5"><label for="studentroll">Student\'s roll: </label></div><div class="col-xs-7 col-md-7"><input type="text" name="studentroll" class="form-control"required></div>';
	}
	else newfield.innerHTML='';
}