import React, { Component } from 'react';
import { Grid, Container, Card, Typography, TextField, Button, Link, InputAdornment, AccountCircle, CircularProgress, Box, CardActions, CardContent } from '@material-ui/core'
import blue from '@material-ui/core/colors/blue';
import './App.css';
import '@fontsource/roboto';
import '@fontsource/abeezee';
import { createMuiTheme, MuiThemeProvider } from '@material-ui/core/styles';
import OpenInNewIcon from '@material-ui/icons/OpenInNew';

const theme = createMuiTheme({
    typography: {
      fontFamily: [
        'ABeeZee'
      ].join(','),
    },
    palette: {
        text: {
            primary: "#FFFFFF",
            secondary: "#AAAAAA",
            info: blue
        },
        primary: blue
    }
});

class Song {
    constructor(artist, title, drugs, profanity, sex_ref, violence, url)
    {
        this.artist = artist;
        this.title = title;
        this.drugs = drugs;
        this.profanity = profanity;
        this.sex_ref = sex_ref;
        this.violence = violence;
        this.url = url;
    }

    formatInfo() {
        function capitalizeFirstLetter(string) {
            return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
          }
        let info = [];
        if (!this.drugs.includes("none")) info.push(capitalizeFirstLetter(this.drugs + " drug references"))
        if (!this.profanity.includes("none")) info.push(capitalizeFirstLetter(this.profanity + " profanity"))
        if (!this.sex_ref.includes("none")) info.push(capitalizeFirstLetter(this.sex_ref + " sexual references"))
        if (!this.violence.includes("none")) info.push(capitalizeFirstLetter(this.violence + " violent references"))
        return info;
    }
}

interface State {
    artist: string;
    title: string;
    apikey: string;
    loaded_song: Song;
    loading: Boolean;
    validate: Boolean;
    invalid_api_key: Boolean;
}

class App extends Component<State> {
    constructor(props) {
    super(props)
        this.state = {
            'artist': '',
            'title': '',
            'apikey': '',
            'loading': false,
            'validate': false,
            'invalid_api_key': false
        }
    }

    handleFieldChange(event) {
        this.setState((state) => {
            return {[event.target.id] : event.target.value}
        })
    }

    handleSubmit() {
        this.state.validate = true;
        this.setState({});
        if (this.state.artist.length > 0
            && this.state.title.length > 0
            && this.state.apikey.length > 0)
            {
                this.invalid_api_key = false;
                this.loading = true;
                let path = `https://flask-service.j894ir4voshjs.us-east-1.cs.amazonlightsail.com/songquery/${this.state.artist}/${this.state.title}/${this.state.apikey}`
                fetch(path, [{'mode': 'cors', 'credentials': 'include'}])
                .then(response => response.json())
                .then(data => {
                    this.loading = false;
                    if (data.meta === 401)
                    {
                        this.state.invalid_api_key = true;
                        this.state.validate = true;
                        this.setState({});  
                    }
                    else if (data.meta === 200)
                    {
                        this.state.invalid_api_key = false;
                        this.state.validate = false;
                        console.log(data)
                        this.loaded_song = new Song(data.artist,
                            data.title,
                            data.drugs,
                            data.profanity,
                            data['sexual references'],
                            data.violence,
                            data.url);
                        this.setState({});  
                    }
                })
            }
    }

    renderInfo() {
        return (
            <div>
            <Typography id="app-name" variant="h1" component="h2" gutterBottom color="primary" fontWeight="fontWeightBold">
                Song analyzer
            </Typography>
            <Typography id="text" variant="h4" component="h2" gutterBottom>
                Be well-informed about the music you're listening to.
            </Typography>
            </div>
        )
    }

    renderInputCard() {
        return (
            <Card id="input-card">
            <form noValidate autoComplete="off" style={{display: 'inline-block'}}>
                <Typography variant="h3" component="h2" gutterBottom>
                    Put in a song
                </Typography>
                <TextField error={this.state.validate && this.state.artist.length === 0} variant="filled" id="artist" label="Artist"
                onChange={(event) => this.handleFieldChange(event)}/>
                <br></br>
                <TextField error={this.state.validate && this.state.title.length === 0} variant="filled" id="title" label="Song title" onChange={(event) => this.handleFieldChange(event)}/>
                <br></br>
                <TextField error={(this.state.validate && this.state.apikey.length === 0) || this.state.invalid_api_key} variant="filled" id="apikey" label="Genius API Key" onChange={(event) => this.handleFieldChange(event)}/>
                <br></br>
                <Button variant="contained" style={{justify:"right"}} color="primary" onClick={() => this.handleSubmit()}>
                    Submit
                </Button>
            </form>
        </Card>)
    }

    renderSongData() {
        if (this.loading) return <CircularProgress />
        else if (this.loaded_song != null)
        {
            let infos = []
            this.loaded_song.formatInfo().forEach((msg) => {
                infos.push(
                <Typography>
                    {msg}
                </Typography>
                )
            })
            return <Card id="info-card" elevation={5}>
                <CardContent>
                    <Typography variant="h2" component="h2">
                        {this.loaded_song.title}
                    </Typography>
                    <Typography variant="h4" component="h2" gutterBottom>
                        by {this.loaded_song.artist}
                    </Typography>
                        {infos}
                </CardContent>
                <CardActions>
                <Link href={this.loaded_song.url} target="_blank">
                    <Button size="small" to={this.loaded_song.url} startIcon={<OpenInNewIcon />}>Full lyrics at Genius</Button>
                </Link>
                </CardActions>
            </Card>;
        }
        else return;
    }

    render() {
        return (
            [<MuiThemeProvider theme={theme}>
                <Box mt={8}>
                    <Grid container direction="column"
                    alignItems="center"
                    jusitfy="space-evenly" spacing={4} xs={12}>
                        <Grid item container direction="row"
                            alignItems="center"
                            justify="space-evenly" spacing={2}>
                            <Grid item xs={12} lg={5} alignItems="stretch">
                            {this.renderInfo()}
                            </Grid>
                            <Grid item xs={12} lg={5} alignItems="stretch">
                            {this.renderInputCard()}
                            </Grid>
                        </Grid>
                        <Grid item xs={5}>
                            {this.renderSongData()}
                        </Grid>
                    </Grid>
                </Box>
            </MuiThemeProvider>]
        );
    }

    renderFooter() {
        return <Box bgcolor="#333333">
            <Container>
                <Grid container xs={12}>
                sheeit

                </Grid>
            </Container>
        </Box>
    }
}

export default App;
