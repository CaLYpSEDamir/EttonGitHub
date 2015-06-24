
// for dynamically add link to li of ul while new repository is imported
// mini-hack
var getCommitsHelper;


(function () {

    'use strict';

    angular.module('GitHubApp', [])

    .config(function($interpolateProvider){
        $interpolateProvider.startSymbol('{[{').endSymbol('}]}');
    })

    .controller('CommitsController', ['$scope', '$http', function($scope, $http){

         $('.mainCheckbox').change(function(){
             $('.applyCheckbox').prop("checked", $('.mainCheckbox').is(':checked'));
         });

         var handleResponseData = function(scope, data){
              scope.commits = data.commits;

              scope.getPagCount = function(){
                  var input = [];
                  for (var i=0;i<data.pag_count;i+=1) input.push(i);
                  return input;
              };

              scope.getRepoId = function(){
                  return data.user_repo_id;
              };
         };

         $scope.getRepository = function(){
              var form =  $('#mainForm');

              if(!form.valid()){
                  return;
              }

             $http.post('/get-repo',
                 {inputUser: $scope.inputUser, inputRepo: $scope.inputRepo}).
                  success(function(data, status, headers, config) {
                      if(!data.commits.length){

                          $scope.commits = [];
                          $scope.getPagCount = function(){
                              return [];
                          };

                          var validator = form.data('validator');
                          validator.showErrors({'error': 'No such repository'});
                      }
                      else{

                          handleResponseData($scope, data);

                          if(data.new_repo){
                              getCommitsHelper = $scope.getCommits;

                              $('#reposUl').append(
                                  "<li><a href='javascript:void(null);' onclick='getCommitsHelper("+
                                  data.user_repo_id +", 0)'>" +
                                  data.new_repo + "</a></li>");
                          }
                      }
                  }).
                  error(function(data, status, headers, config) {
                      alert('Error occured!');
                  });
        };

         $scope.getCommits = function(userRepoId, count){
             $http.post('/get-commits',
                 {userRepoId: userRepoId, count: count}).
                 success(function(data, status, headers, config){

                     handleResponseData($scope, data);

                 }).
                 error(function(data, status, headers, config) {
                     alert('Error occured!');
                 });
        };

        $scope.deleteCommits = function(){

            var result = [];
            $('.applyCheckbox').each(function(i, el){
                var $ths = $(el);
                if (!$ths.is(':checked')){
                    return;
                }
                result.push($ths.data('value'));
            });
            if (!result.length){
                return;
            }

             $http.post('/delete-commits',
                 {commit_ids: result}).
                 success(function(data, status, headers, config){

                     handleResponseData($scope, data);
                 }).
                 error(function(data, status, headers, config) {
                     alert('Error occured!');
                 });
        };

    }]);

}());