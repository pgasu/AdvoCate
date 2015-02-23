$(function() {

					function getCookie(name) {
						var cookieValue = null;
						if (document.cookie && document.cookie != '') {
							var cookies = document.cookie.split(';');
							for (var i = 0; i < cookies.length; i++) {
								var cookie = jQuery.trim(cookies[i]);
								// Does this cookie string
								// begin with the name we
								// want?
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
						// these HTTP methods do not require
						// CSRF protection
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

					$('.dropdown-toggle').dropdown();

					$('input[name="testoption"]').on('click',function() {
			//		$('#trainingoption').on('click', 'input[name="testoption"]', function(){  -- another way of doing it
						var $this = $(this);
						$this.removeAttr('disabled');
						$this.siblings('input').children().attr('disabled');
						
					});
										
								/*		if (
												checkedOption.removeAttr('disabled');
												checkedOption.siblings('input').children().attr('disabled');
												$(checkedOption.attr("id") == "trainingfile") {
													testFileOption.prop('disabled',	false);
													crossValidationFolds.prop('disabled', true);
													percentageSplitForValidation.prop('disabled',true);
										} else if ($(
												'input[name="testoption"]:checked')
												.attr("id") == "CrossValidation") {
											$("#testfile").prop('disabled',
													true);
											$("#Fold").prop('disabled', false);
											$("#Percentage").prop('disabled',
													true);

										} else if ($(
												'input[name="testoption"]:checked')
												.attr("id") == "PercentageSplit") {
											$("#testfile").prop('disabled',
													true);
											$("#Fold").prop('disabled', true);
											$("#Percentage").prop('disabled',
													false);

										} else {
											$("#testfile").prop('disabled',
													true);
											$("#Fold").prop('disabled', true);
											$("#Percentage").prop('disabled',
													true);
										}*/
										

					// Function to set the height of training data table based
					// on window size
					(function setHeight() {
						var headerHeight = $('.container').outerHeight();
						var totalHeight = $(window).height();
						$('#dataTable').css({
							'height' : totalHeight - headerHeight - 10 + 'px'
						});
					})();

					// call the setHeight function, everytime window is resized
					$(window).on('resize', function() {
						setHeight();
					});
					// call it for the first time
				//	setHeight();

					// Script to deal with when the training file is uploaded
					$('#trainingfile')
							.change(
									function() {
										var file = this.files[0];
										// FileReader Object reads the content
										// of file as text string into memory
										var reader = new FileReader();
										reader.readAsText(file);
										reader.onload = function(event) {
											var csv = event.target.result;
											var data = $.csv.toArrays(csv);

											var instances = 0
											var attributes = 0
											for ( var head in data[0]) {
												attributes += 1;
											}
											for (var row = 1; row < data.length; row++) {
												instances += 1;
											}
											$('#instances').html(instances);
											$('#Attributes').html(attributes);

											$('#saveChanges').toggle();
											$('#saveChanges').prop("disabled",
													true);
											var $container = $('#dataTable');
											// HandsonTable library to display
											// interactive data table
											$container.handsontable({
												data : data,

											});
										};

										// Posting file to the server side using
										// formdata
										var formdata = new FormData();
										formdata.append("trainingfile", file);
										$
												.ajax({

													type : "POST",
													url : "http://127.0.0.1:8000/CategoryModeler/preprocess/",
													dataType : "json",
													async : true,
													processData : false, 
													contentType : false,
													data : formdata,
													success : function(response) {

													}
												});

										var $container = $('#dataTable');
										$container.handsontable({
											afterChange : function(change,
													source) {
												if (source === 'loadData') {
													return;
												} else {
													$('#saveChanges').prop(
															"disabled", false);
												}

											}

										});

									});

					$('#saveChanges').click(
									function() {
										//So after the execution it doesn't refresh back
										event.preventDefault();
										var handsontable = $('#dataTable').data('handsontable');
												$.ajax({
													type : "POST",
													url : "http://127.0.0.1:8000/CategoryModeler/preprocess/",
													dataType : "json",
													async : true,
													processData : false,
													contentType : false,
													data : JSON.stringify(handsontable.getData()),
													success : function(response) {

													}

												});
									});

				});
