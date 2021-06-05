import React, { Component } from 'react';
import { Grid, Card, Typography, TextField, Button } from '@material-ui/core'
import logo from './logo.svg';
import './App.css';
import '@fontsource/roboto';

interface State {
    artist: string;
    title: string;
}

class App extends Component<State> {
    constructor(props) {
    super(props)
        this.state = {'artist': '', 'title': ''}
    }

    handleFieldChange(event) {
        this.setState((state) => {
            return {[event.target.id] : event.target.value}
        })
    }

    handleSubmit() {
        let path = `http://localhost:8000/songquery/${this.state.artist}/${this.state.title}/`
        console.log(path)
        fetch(path, [, {'credentials': 'include'}])
            .then(response => response.json())
            .then(data => console.log(data))
    }

    render() {
        return (
            <Grid container direction="column"
                justify="center"
                alignItems="center">
                <Grid item xs={6}>
                    <Card variant="outlined">
                        <Typography component="h1" gutterBottom>
                            song analyzer
                        </Typography>
                        <form noValidate autoComplete="off">
                            <TextField id="artist" label="Artist" onChange={(event) => this.handleFieldChange(event)}/>
                            <TextField id="title" label="Song title" onChange={(event) => this.handleFieldChange(event)}/>
                            <Button variant="contained" color="primary" onClick={() => this.handleSubmit()}>
                                Submit
                            </Button>
                        </form>
                    </Card>
                </Grid>
            </Grid>
        );
    }
}

export default App;
