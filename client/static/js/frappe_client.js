
USERLIST = "/users/";

angular.module("frappeApp", ["ngRoute"])
    .controller("FrappeController", ["$scope", function($scope) {

        $scope.loadUsers = function() {
            window.location.replace("#/" + $scope.frappeText +"/");
        };
    }])
    .config(["$routeProvider",
        function($routeProvider) {
            $routeProvider.when("/:frappeURL*", {
                template: '<div class="list-group">' +
                               '<a ng-repeat="user in result.users" href="#/{{ url }}/{{ external_id }}/" class="list-group-item">Cras justo odio</a>' +
                          '</div>',
                controller: function ($scope, $http, $routeParams) {
                    $http({method: "GET", url: $routeParams.frappeURL + USERLIST})
                        .success(function(data, status) {
                            $scope.users = data;
                            $scope.url = $routeParams.frappeURL;
                        })
                }
            }).otherwise({
                redirectTo: '/'
            });
            // configure html5 to get links working on jsfiddle
            //$locationProvider.html5Mode(true);
        }]);