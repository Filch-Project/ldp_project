from django import forms


<form action="/draft/" method="post">
    <label for="draft">Enter Your Draft Position: </label>
    <input id="draft" type="text" name="draft" value="{{ draft }}">
    <input type="submit" value="OK">
</form>
