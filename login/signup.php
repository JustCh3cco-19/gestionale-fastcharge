<?php 
session_start();
?>

<!DOCTYPE html>
<html>
<head>
    <title>Registrati</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
    <style type="text/css">
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f3f3f3;
        }

        .signup-container {
            width: 300px;
            padding: 20px;
            background: white;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        .signup-container h2 {
            margin-bottom: 20px;
        }

        .signup-container label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            text-align: left;
        }

        .signup-container input[type="text"],
        .signup-container input[type="password"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
        }

        .signup-container button {
            width: 100%;
            padding: 10px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        .signup-container button:hover {
            background-color: #0056b3;
        }

        .signup-container a {
            display: block;
            margin-top: 10px;
            color: #007BFF;
            text-decoration: none;
        }

        .signup-container a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="signup-container">
        <h2>Registrati</h2>
        <form action="includes/signup.inc.php" method="post">
            <label for="name">Username</label>
            <input type="text" class="form-control" id="name" name="uid" placeholder="Username">

            <label for="mail">Email</label>
            <input type="text" class="form-control" id="mail" name="mail" placeholder="Email">

            <label for="password">Password</label>
            <input type="password" class="form-control" id="password" name="pwd" placeholder="Password">

            <label for="password-repeat">Ripeti Password</label>
            <input type="password" class="form-control" id="password-repeat" name="pwd-repeat" placeholder="Ripeti Password">

            <button type="submit" class="btn btn-primary" name="signup-submit">Registrati</button>
        </form>
        <a href="index.php">Accedi</a>
    </div>
</body>
</html>
