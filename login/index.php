<?php 
session_start();
?>

<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
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

        .login-container {
            width: 300px;
            padding: 20px;
            background: white;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        .login-container h2 {
            margin-bottom: 20px;
        }

        .login-container label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            text-align: left;
        }

        .login-container input[type="text"],
        .login-container input[type="password"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 4px;
        }

        .login-container button {
            width: 100%;
            padding: 10px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        .login-container button:hover {
            background-color: #0056b3;
        }

        .login-container a {
            display: block;
            margin-top: 10px;
            color: #007BFF;
            text-decoration: none;
        }

        .login-container a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login Page</h2>
        <form action="includes/login.inc.php" method="post">
            <label for="exampleInputEmail1">Username/Email</label>
            <input type="text" class="form-control" id="exampleInputEmail1" name="mailuid" placeholder="Username/Email">

            <label for="exampleInputPassword1">Password</label>
            <input type="password" class="form-control" id="exampleInputPassword1" name="pwd" placeholder="Password">

            <button type="submit" class="btn btn-primary" name="login-submit">Accedi</button>
        </form>
        <a href="signup.php">Registrati</a>
    </div>

    <?php 
    if (isset($_SESSION["userId"])) {
        echo '<div style="margin-top: 20px; text-align: center;">';
        echo '<form action="includes/logout.inc.php" method="post">';
        echo '<button type="submit" class="btn btn-secondary" name="logout-submit">Logout</button>';
        echo '</form>';
        echo '</div>';
    }
    ?>
</body>
</html>
