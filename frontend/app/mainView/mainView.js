'use strict';

angular.module('myApp.mainView', ['ngRoute'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/mainView', {
    templateUrl: 'mainView/mainView.html',
    controller: 'MainViewCtrl'
  });
}])

.controller('MainViewCtrl', ["$scope","$http",
	function($scope,$http) {
		$scope.photoSets=[];
		$scope.photos=[];

		$http.get('/photosets/all').success(function(data) {
		  $scope.photoSets = data["photosets"];
		  //console.log($scope.photoSets)
		});

		$scope.displaySet=function(photoSet){
			var set_id=photoSet.set_id;
			console.log(photoSet.expanded);
			if(typeof $scope.photos[set_id]!="undefined"){
				photoSet.expanded=!photoSet.expanded;
				return 0;
			}

			$http.get("/photosets/"+set_id).success(function(data){
				$scope.photos[set_id]=data["photos"];
				console.log($scope.photos);
				photoSet.expanded=!photoSet.expanded;
			})
		}
	}]
);