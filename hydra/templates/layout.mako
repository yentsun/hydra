<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>${self.title()} - Hydra</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="">
    <!-- Le styles -->
    <link href="/static/css/bootstrap.css" rel="stylesheet">
    <style type="text/css">
        body {
            padding-top: 40px;
            padding-bottom: 40px;
            background-color: #f5f5f5;
        }
    </style>
    <!-- HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
    <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
    <!-- Fav and touch icons -->
    <link rel="shortcut icon" href="/static/favicon.ico">
</head>
<body>
<div class="navbar">
  <div class="navbar-inner">
      <a class="brand" href="#">Hydra</a>
      <a class="btn btn-danger pull-right" href="/logout">выйти</a>



  </div>
</div>
<div id="content" class="row container">
    <div class="span12">
    ${next.body()}
    </div>
</div>
<script src="/static/js/jquery.min.js" type="text/javascript"></script>
<script src="/static/js/bootstrap.min.js" type="text/javascript"></script>
% if hasattr(self,'js'):
${self.js()}
% endif
</body>
</html>