$(function() {
	
		function getCookie(name) {
			var cookieValue = null;
			if (document.cookie && document.cookie != '') {
				var cookies = document.cookie.split(';');
				for (var i = 0; i < cookies.length; i++) {
					var cookie = jQuery.trim(cookies[i]);
					// Does this cookie string begin with the name we want?
					if (cookie.substring(0, name.length + 1) == (name + '=')) {
						cookieValue = decodeURIComponent(cookie
								.substring(name.length + 1));
						break;
					}
				}
			}
			return cookieValue;
		}

		var csrftoken = getCookie('csrftoken');
		
		function csrfSafeMethod(method) {
			// these HTTP methods do not require CSRF protection
			return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
		}

		$.ajaxSetup({			
			beforeSend : function(xhr, settings) {
				if (!csrfSafeMethod(settings.type)
						&& !this.crossDomain) {
					xhr.setRequestHeader("X-CSRFToken", csrftoken);
				}
			}
		});
		
		// Function to set the height of training data table based on window size
		function setTrainingSamplesTableHeight() {
			var headerHeight = $('#top-part').outerHeight();
			var totalHeight = $(window).height();
			$('#trainingdataTable').css({'height' : totalHeight - headerHeight -140 + 'px'});
		};
		
		function setSignatureFileDetailsHeight() {
			var headerHeight = $('#top-part').outerHeight();
			var totalHeight = $(window).height();
			$('#signaturefiledetails').css({'height' : totalHeight - headerHeight -140 + 'px'});
		};
// Script for navbar
		
		var loc = window.location.href;
		
		$('.nav.nav-pills.nav-justified > li').each(function(){
			var $this = $(this)
			if (loc.match('http://127.0.0.1:8000' + $this.children().attr('href'))){
				$this.addClass("active");
				$this.siblings().removeClass("active");
			}
		});

// Script for sign in and register tab
		$('#session').click(function() {
			// Conditional states allow the dropdown box appear and disappear
			if ($('#signin-dropdown').is(":visible")) {
				$('#signin-dropdown').hide();
				$('#session').removeClass('active'); // When the dropdown is not
				$('#register-dropdown')	.hide();									// visible removes the class
														// "active"
			} else {
				$('#signin-dropdown').show()
				$('#session').addClass('active'); // When the dropdown is visible
													// add class "active"
			}
			return false;
		});
		
		$('#register-link').on('click', function(e){
			$('#register-dropdown').show();
			$('#signin-dropdown').hide();
		});
		
		$('#signin-link-bak').on('click', function(e){
			$('#register-dropdown').hide();
			$('#signin-dropdown').show();
		});

		// Allow to hide the dropdown box if you click anywhere on the document.
		$('#signin-dropdown').click(function(e) {
			e.stopPropagation();
		});
		$('#register-dropdown').click(function(e) {
			e.stopPropagation();
		});
		$(document).click(function() {
			$('#signin-dropdown').hide();
			$('#session').removeClass('active');
			$('#register-dropdown').hide();
		});
		
		$('#Signin').on('click', function(e){
			if ($('#username').val() !="" && $('#password').val() !=""){
				e.preventDefault();
				var $this = $('#signindetails');
				$.post("http://127.0.0.1:8000/AdvoCate/accounts/auth/", $this.serialize(), function(response){
					if ('error' in response){
						$('p#signinerror').html(response['error']);					
					}
					else{
						$('div#topnav').html("<div id=\"logoutsession\"><strong>Welcome "+response['user_name']+" &nbsp; &nbsp;</strong><a id=\"logout-link\" href=\"/AdvoCate/accounts/logout/\"> Sign out </a></div>");
					}
						
				});			
			}

		});

// Script for 'Training Samples' page	
		
		if (loc.match('http://127.0.0.1:8000/AdvoCate/trainingsample/')){
			
			
		
		
			$('input[name="choosetrainingfile"]').on('click', function(){
				var $this = $(this);
				$this.next().children().removeAttr('disabled');
				$this.siblings('input').next().children().attr('disabled', 'disabled');
				
				if ($this.attr('value')=='option2'){
					$('#newtrainingdatasetdetails').show();
				}
				else{
					$('#newtrainingdatasetdetails').hide();
				}
				
			});
			
	
			
			function firstRowRenderer(instance, td, row, col, prop, value, cellProperties) {
				  Handsontable.renderers.TextRenderer.apply(this, arguments);
				  td.style.fontWeight = 'bold';
				  td.style.background = 'gainsboro';
				}
			
			var settings1 = {
				contextMenu: true,
				afterChange: function(change, source){
					if (source === 'loadData') {
						return;
					} 
					
					$('#saveChanges').show();
				},
				cells: function(row, col, prop){
					var cellProperties = {};
					if (row==0){
						cellProperties.readOnly = true;
						cellProperties.renderer = firstRowRenderer;
					}
					return cellProperties;
				}
				
			};

			
			var trainingdatacontainer = document.getElementById('trainingdataTable'),
			hot;
			hot = new Handsontable(trainingdatacontainer, settings1);
	
			//Script to deal with when the existing training file is selected
			$('#existingtrainingfiles').on('change', function(){
				$('#instanceslabel').show();
				$('#attributeslabel').show();
				
				
				var filepkey = this.value;
				var filename = $('#existingtrainingfiles>option:selected').text();
				var data={};
				data[1] = filepkey;
				data[2] = filename;
				$.post("http://127.0.0.1:8000/AdvoCate/trainingsample/", data, function(response){
					var trainingdata = $.csv.toArrays(response);
					$('#instances').html(trainingdata.length-1);
					$('#Attributes').html(trainingdata[0].length);
					
					$('#trainingdataTable').show();
					hot.loadData(trainingdata);
				});
	
				
				
			});
	
			
			
			// Script to deal with when the training file is uploaded
			$('#trainingfile').on('change', function() { 
				$('#instanceslabel').show();
				$('#attributeslabel').show();
				
				var ext = this.value.match(/\.(.+)$/)[1];
				var newtrainingdataset = this.files[0];
				if (ext == 'csv'){
					// FileReader Object reads the content
					// of file as text string into memory
					var reader = new FileReader();
					
					reader.onload = function(event) {
						var csv = reader.result;  // I can also write event.target.result
						var trainingdata = $.csv.toArrays(csv);
					
						$('#instances').html(trainingdata.length-1);
						$('#Attributes').html(trainingdata[0].length);
						
						$('#trainingdataTable').show();
						hot.loadData(trainingdata);
	
					};
					reader.readAsText(newtrainingdataset);
					
				}
				else{
					
				}
						
				// Posting file to the server side using formdata
				var formdata = new FormData();
				formdata.append("trainingfile", newtrainingdataset);
				$.ajax({
					type : "POST",
					url : "http://127.0.0.1:8000/AdvoCate/trainingsample/",
					async : true,
					processData : false, 
					contentType : false,
					data : formdata,
					success : function(response) {
						//newfile = response['training File'];
						var trainingdata = $.csv.toArrays(response);
						$('#instances').html(trainingdata.length-1);
						$('#Attributes').html(trainingdata[0].length);
						
						$('#trainingdataTable').show();
						hot.loadData(trainingdata);
	
					}
				});
	
			});
			

	
			setTrainingSamplesTableHeight();
			// call the setHeight function, every time window is resized
			$(window).on('resize', function() {
				setTrainingSamplesTableHeight();
			});
			
			
			$('#savetrainingdatadetails').on('click', function(e){
				e.preventDefault();
				var $this = $('#newtrainingdatasetdetails');
				$.post("http://127.0.0.1:8000/AdvoCate/savetrainingdatadetails/", $this.serialize(), function(response){
					alert(response);
				});
				
			});
	
			$('#saveChanges').on('click', function() { 
				//So after the execution it doesn't refresh back
				console.log(JSON.stringify(hot.getData()));
				event.preventDefault();
						$.ajax({
							type : "POST",
							url : "http://127.0.0.1:8000/AdvoCate/saveNewTrainingVersion/",
							async : true,
							processData : false,
							contentType : false,
							data : JSON.stringify(hot.getData()),
							success : function(response) {
	
							}
	
						});
			});
		
		}
		
// Script for 'Signature file' page		
		
		if (loc.match('http://127.0.0.1:8000/AdvoCate/signaturefile/')){
			
			setSignatureFileDetailsHeight();
			
			$(window).on('resize', function() {
				setSignatureFileDetailsHeight();
			});
			
			$('.dropdown-toggle').dropdown();
			
			$('input[name="validationoption"]').on('click',function() {
				var $this = $(this);
				$this.next().children().removeAttr('disabled');
				$this.siblings('input').next().children().attr('disabled', 'disabled');
				
			});
			
			$('#createsignaturefile').on('click', function(e){
				if ($('#classifiertype').val() !="" && $('#targetattribute').val() !=undefined && $('input[name=validationoption]:checked').val() !=null){
					e.preventDefault();
					var $this = $('#trainingoptions');
					var formData = new FormData($this[0]);
					$.ajax({
						type : "POST",
						url : "http://127.0.0.1:8000/AdvoCate/signaturefile/",
						async : true,
						processData : false, 
						contentType : false,
						data : formData,
						success : function(response) {
							
							$('#validationscore').html("<b>Validation score:  </b>" + response['score']);
							
							$('#signaturefiledetailsoptions').show();
							var a =	"<table style=\"width:100%\" ><tr><th> Class </th><th> Mean Vector </th></tr>"
							for (var i=0; i<response['listofclasses'].length; i++){
								a = a+ "<tr><td>" +  	response['listofclasses'][i] + "</td><td>" + 	response['meanvectors'][i] + "</td></tr>";						
							} 
							a = a+	"</table>";	
							$('#meanvectors').html(a);
							
							var b = "<table style=\"width:100%\" ><tr><th> Class </th><th> Variance </th></tr>"
							for (var i=0; i<response['listofclasses'].length; i++){
								b = b + "<tr><td>" + response['listofclasses'][i] + "</td><td>" + response['variance'][i] + "</td></tr>";						
							} 
							b = b +	"</table>";	
							$('#variance').html(b);
							
							$('#meanvectors').hide();
							$('#variance').hide();
		
						}
		
					});
				}

			});
			
			$('input[name="signaturefiledetailsoptions"]').on('click', function(e){
				
				var detailsoption = $('input[name="signaturefiledetailsoptions"]:checked').val();
				console.log(detailsoption);
				if (detailsoption=='1'){
					$('#meanvectors').show();
					$('#variance').hide();
					$('#confusionmatrix').hide();					
				}					
				else if (detailsoption=='2'){
					console.log(detailsoption);
					$('#meanvectors').hide();
					$('#variance').show();
					$('#confusionmatrix').hide();
				}
				else if (detailsoption=='3'){
					$('#meanvectors').hide();
					$('#variance').hide();
					$('#confusionmatrix').show();
				}
				else {
					$('#meanvectors').hide();
					$('#variance').hide();
					$('#confusionmatrix').hide();
					
				}
			});
		}
		
		
//Script for visualization
		
/*		$('#creategraph').on('click', function(){
			var G = jsnx.Graph();
			G.add_nodes_from([
			                  ['Built Space', {color: 'red'}, {count: 18}],
			                  [2, {color: 'blue'}],
			
			]);
			G.add_edges_from([['Built Space',2]]);
			
			console.log(G.nodes(true));
			
			
			
			jsnx.draw(G, {
				element: '#networkGraph',
				with_labels: true,
				  node_style: {
				      fill: function(d) {
				          return d.data.color;
				      }
				  }
				});
			
		});*/
		


	});
